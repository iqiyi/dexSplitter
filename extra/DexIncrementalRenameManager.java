/*
 * Copyright (C) 2016 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.android.builder.internal.packaging;

import com.android.SdkConstants;
import com.android.annotations.NonNull;
import com.android.builder.files.RelativeFile;
import com.android.ide.common.res2.FileStatus;
import com.google.common.base.Preconditions;
import com.google.common.base.Verify;
import com.google.common.collect.BiMap;
import com.google.common.collect.HashBiMap;
import com.google.common.collect.ImmutableMap;
import com.google.common.io.Closer;
import java.io.Closeable;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Deque;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Properties;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * Keeps track of incremental, renamed dex files.
 *
 * <p>Dex files need to be renamed when packaged. When a dex file is incrementally modified (added,
 * modified, deleted), it is necessary to incrementally propagate that modification to the package.
 *
 * <p>This class keeps a map of dex files and their new names in the archive. When a dex file
 * is incrementally modified, this class computes what the incremental change to the archive needs
 * to be, with respect to the dex file.
 *
 * <p>For example, if an archive is empty and file {@code a.dex} is added, then the manager will
 * say {@code classes.dex} needs to be added and {@code classes.dex} refers to {@code a.dex}.
 *
 * <p>If, later, archive {@code b.dex} is added, then the manager will say {@code classes2.dex}
 * needs to be added and {@code classes2.dex} refers to {@code b.dex}.
 *
 * <p>Then, if {@code a.dex} is removed, the manager will say {@code classes.dex} needs to be
 * updated and {@code classes.dex} now refers to {@code b.dex}.
 */
class DexIncrementalRenameManager implements Closeable {

    private enum BucketAction {
        NOTHING,
        UPDATE,
        DELETE,
        CREATE
    }

    private static class Bucket {

        RelativeFile file;
        String nameInDex;
        BucketAction action;

        Bucket(RelativeFile file, String nameInDex, BucketAction action) {
            this.file = file;
            this.nameInDex = nameInDex;
            this.action = action;
        }
    }

    /**
     * Name of state file.
     */
    private static final String STATE_FILE = "dex-renamer-state.txt";

    /**
     * Prefix for property that has the base name of the relative file.
     */
    private static final String BASE_KEY_PREFIX = "base.";

    /**
     * Prefix for property that has the name of the relative file.
     */
    private static final String FILE_KEY_PREFIX = "file.";

    /**
     * Prefix for property that has the name of the renamed file.
     */
    private static final String RENAMED_KEY_PREFIX = "renamed.";

    /**
     * Mapping between relative files and file names.
     */
    @NonNull
    private final BiMap<RelativeFile, String> mNameMap;

    /**
     * Temporary directory to use to store and retrieve state.
     */
    @NonNull
    private final File mIncrementalDir;

    /**
     * Is the manager closed?
     */
    private boolean mClosed;

    /**
     * Creates a new rename manager.
     *
     * @param incrementalDir an incremental directory to store state.
     * @throws IOException failed to read incremental state
     */
    DexIncrementalRenameManager(@NonNull File incrementalDir) throws IOException {
        Preconditions.checkArgument(incrementalDir.isDirectory(), "!incrementalDir.isDirectory()");

        mNameMap = HashBiMap.create();
        mIncrementalDir = incrementalDir;
        mClosed = false;

        readState();
    }

    /**
     * Reads previously saved incremental state.
     *
     * @throws IOException failed to read state; not thrown if no state exists
     */
    private void readState() throws IOException {
        File stateFile = new File(mIncrementalDir, STATE_FILE);
        if (!stateFile.isFile()) {
            return;
        }

        Properties props = new Properties();
        Closer closer = Closer.create();
        try {
            props.load(closer.register(new FileReader(stateFile)));
        } catch (Throwable t) {
            throw closer.rethrow(t);
        } finally {
            closer.close();
        }

        for (int i = 0; ; i++) {
            String baseKey = BASE_KEY_PREFIX + i;
            String fileKey = FILE_KEY_PREFIX + i;
            String renamedKey = RENAMED_KEY_PREFIX + i;

            String base = props.getProperty(baseKey);
            String file = props.getProperty(fileKey);
            String rename = props.getProperty(renamedKey);

            if (base == null || file == null || rename == null) {
                break;
            }

            RelativeFile rf = new RelativeFile(new File(base), new File(file));
            mNameMap.put(rf, rename);
        }
    }

    /**
     * Writes incremental state.
     *
     * @throws IOException failed to write state
     */
    private void writeState() throws IOException {
        File stateFile = new File(mIncrementalDir, STATE_FILE);

        Properties props = new Properties();
        int currIdx = 0;
        for (BiMap.Entry<RelativeFile, String> entry : mNameMap.entrySet()) {
            props.put(BASE_KEY_PREFIX + currIdx, entry.getKey().getBase().getPath());
            props.put(FILE_KEY_PREFIX + currIdx, entry.getKey().getFile().getPath());
            props.put(RENAMED_KEY_PREFIX + currIdx, entry.getValue());
            currIdx++;
        }

        Closer closer = Closer.create();
        try {
            props.store(closer.register(new FileWriter(stateFile)), null);
        } catch (Throwable t) {
            throw closer.rethrow(t);
        } finally {
            closer.close();
        }
    }

    /**
     * Updates the state of the manager with file changes.
     *
     * @param files the files that have changed
     * @return the changed in the packaged files
     * @throws IOException failed to process the changes
     */
    @NonNull
    Set<PackagedFileUpdate> update(@NonNull ImmutableMap<RelativeFile, FileStatus> files)
            throws IOException {

        // Make list of new files and ensure classes.dex is/are the first (there could be multiple)
        Deque<RelativeFile> newFiles =
                files.entrySet()
                        .stream()
                        .filter(e -> e.getValue() == FileStatus.NEW)
                        .map(Map.Entry::getKey)
                        .sorted(
                                Comparator.comparing(
                                        RelativeFile::getOsIndependentRelativePath,
                                        new DexNameComparator()))
                        .collect(Collectors.toCollection(LinkedList::new));

        // Build a list with buckets that represent the dex files we have before the updates.
        // Mark updated buckets, remove entries from deleted buckets and fill them with new files
        // if there are any new files left.
        DexFileNameSupplier supplier = new DexFileNameSupplier();
        List<Bucket> buckets = new ArrayList<>();
        //for (int i = 0; i < mNameMap.size(); i++) {
        //    String nameInDex = supplier.get();
        //    RelativeFile rf = mNameMap.inverse().get(nameInDex);
        //    Verify.verify(rf != null, "No file known for: " + nameInDex);
        //
        //    // If the first currently mapped file is not classes.dex, but the first file to add
        //    // is classes.dex, we'll replace the file to make sure classes.dex is mapped to
        //    // classes.dex.
        //    if (nameInDex.equals(SdkConstants.FN_APK_CLASSES_DEX)
        //            && !getOsIndependentFileName(rf).equals(SdkConstants.FN_APK_CLASSES_DEX)
        //            && !newFiles.isEmpty()
        //            && getOsIndependentFileName(newFiles.getFirst())
        //                    .equals(SdkConstants.FN_APK_CLASSES_DEX)) {
        //        Verify.verify(i == 0);
        //        buckets.add(new Bucket(newFiles.removeFirst(), nameInDex, BucketAction.UPDATE));
        //
        //        // Make sure rf will be eventually added somewhere :)
        //        newFiles.add(rf);
        //        continue;
        //    }
        //
        //    Bucket newBucket = new Bucket(rf, nameInDex, BucketAction.NOTHING);
        //
        //    FileStatus status = files.get(rf);
        //    if (status == FileStatus.REMOVED) {
        //        if (newFiles.isEmpty()) {
        //            newBucket.file = rf;
        //            newBucket.action = BucketAction.DELETE;
        //        } else {
        //            newBucket.file = newFiles.removeFirst();
        //            newBucket.action = BucketAction.UPDATE;
        //        }
        //    } else if (status == FileStatus.CHANGED) {
        //        newBucket.file = rf;
        //        newBucket.action = BucketAction.UPDATE;
        //    }
        //
        //    buckets.add(newBucket);
        //}

        if (newFiles.isEmpty()) {
            // Remove empty buckets from the middle of the list by iteratively exchanging the
            // left-most empty space with the right-most used space until all empty buckets are
            // at the end.
            for (int emp = 0, use = buckets.size() - 1; ; emp++, use--) {
                for (;
                        emp < buckets.size() && buckets.get(emp).action != BucketAction.DELETE;
                        emp++) ;
                for (; use >= 0 && buckets.get(use).action == BucketAction.DELETE; use--) ;
                if (emp > use) {
                    break;
                }

                buckets.get(emp).file = buckets.get(use).file;
                buckets.get(emp).action = BucketAction.UPDATE;
                buckets.get(use).action = BucketAction.DELETE;
            }
        } else {
            // Add remaining new files.
            newFiles.forEach(
                    //nf -> buckets.add(new Bucket(nf, supplier.get(), BucketAction.CREATE)));
                    nf -> {
                        buckets.add(new Bucket(nf, nf.getOsIndependentRelativePath()+".dex", BucketAction.CREATE));
                        System.out.println("build dex name  -> " + nf.getOsIndependentRelativePath()+".dex");
                    });
        }

        // Update state and compute the return set.
        mNameMap.clear();
        return buckets.stream()
                .peek(
                        b -> {
                            if (b.action != BucketAction.DELETE) {
                                mNameMap.put(b.file, b.nameInDex);
                            }
                        })
                .map(
                        b -> {
                            switch (b.action) {
                                case CREATE:
                                    return new PackagedFileUpdate(
                                            b.file, b.nameInDex, FileStatus.NEW);
                                case DELETE:
                                    return new PackagedFileUpdate(
                                            b.file, b.nameInDex, FileStatus.REMOVED);
                                case NOTHING:
                                    return null;
                                case UPDATE:
                                    return new PackagedFileUpdate(
                                            b.file, b.nameInDex, FileStatus.CHANGED);
                                default:
                                    throw new AssertionError();
                            }
                        })
                .filter(Objects::nonNull)
                .collect(Collectors.toSet());

    }

    @Override
    public void close() throws IOException {
        if (mClosed) {
            return;
        }

        mClosed = true;
        writeState();
    }

    /**
     * Obtains the file name in the OS-independent relative path in a relative file.
     *
     * @param file the file, <i>e.g.</i>, {@code foo/bar}
     * @return the file name, <i>e.g.</i>, {@code bar}
     */
    @NonNull
    private static String getOsIndependentFileName(@NonNull RelativeFile file) {
        String[] pathSplit = file.getOsIndependentRelativePath().split("/");
        return pathSplit[pathSplit.length - 1];
    }

    /** Comparator that compares dex file names placing classes.dex always in front. */
    private static class DexNameComparator implements Comparator<String> {

        @Override
        public int compare(String f1, String f2) {
            if (f1.equals(SdkConstants.FN_APK_CLASSES_DEX)) {
                return -1;
            } else if (f2.equals(SdkConstants.FN_APK_CLASSES_DEX)) {
                return 1;
            } else {
                return f1.compareTo(f2);
            }
        }
    }
}

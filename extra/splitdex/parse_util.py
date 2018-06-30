import os, shutil, subprocess, zipfile
import base_config

def gradle_clean():
    ret = subprocess.call(base_config.gradlew_path + ' -q -b ' + base_config.project_dir + '/build.gradle'
                                                                                           '  clean', shell=True)
    if ret == 0:
        print 'gradle clean sucess!'
    else:
        print 'gradle clean failed!'


def gradle_assemble_release_withhack(ishack):
    extra_para = ' -P' + base_config.hack_para if ishack else ''
    print base_config.gradlew_path + ' -q -b ' + base_config.project_dir + 'build.gradle' + extra_para + ' --no-daemon assembleRelease -s'
    ret = subprocess.call(
        base_config.gradlew_path + ' -q -b ' + base_config.project_dir + 'build.gradle' + extra_para + ' --no-daemon assembleRelease ' + '-s',
        shell=True)
    if ret == 0:
        print 'gradle assembleRelease sucess!'
    else:
        print 'gradle assembleRelease failed!'


def parse_jar_2tempfile(apk_file_path, file_name):
    if not os.path.exists(apk_file_path):
        print('file not found: ' + apk_file_path)
        return

    proc = subprocess.Popen([base_config.aapt_file_path, 'l', '-v', apk_file_path], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    details = proc.stdout.readlines()
    write_list_2file(details, file_name)


def get_module_sourcecode_form_jar(filepath):
    parse_jar_2tempfile(filepath, base_config.temp_jar_file)
    if not os.path.exists(base_config.temp_jar_file):
        print('file not found: ' + base_config.temp_jar_file)
        return
    file_list = []
    file_object = open(base_config.temp_jar_file, 'rU')
    try:
        for line in file_object:
            if line.find('.class') >= 0:
                filepath = parse_filepath(line)
                if filepath.endswith('BuildConfig.class'):
                    filepath = filepath.replace('BuildConfig.class', 'R.class')
                file_list.append(filepath)
    finally:
        file_object.close()
    return file_list


def get_host_project_classes():
    build_dir = '/build/intermediates/classes/release'
    host_projec_classpath = base_config.app_host_module_dir + build_dir + "/"+ base_config.app_package_path

    main_classes_list = []
    for root, dirs, files in os.walk(host_projec_classpath, topdown=False):
        for name in files:
            if name.endswith('.class'):
                filepath = os.path.join(root, name)
                filepath = filepath.replace('\\', '/')

                if name.endswith('TestClassForMainDex.class'):
                    continue
                if filepath.endswith('BuildConfig.class'):
                    continue
                main_classes_list.append(filepath.replace(base_config.app_host_module_dir + build_dir + '/', ''))

    host_project_libs_dir = base_config.app_host_module_dir + base_config.lib_endpath
    if not os.path.exists(host_project_libs_dir):
        return main_classes_list

    for filepath in os.listdir(host_project_libs_dir):
        if filepath.endswith('.jar'):
            main_classes_list += get_module_sourcecode_form_jar(host_project_libs_dir + filepath)
    return main_classes_list


def get_library_module_classes(moudle_relative_path):
    project_allclasses_list = []

    module_project_libs_dir = base_config.project_dir + moudle_relative_path + base_config.lib_endpath
    module_project_source_code_dir = base_config.project_dir + moudle_relative_path + base_config.library_module_source_jar_path
    project_allclasses_list += get_module_sourcecode_form_jar(module_project_source_code_dir)

    if not os.path.exists(module_project_libs_dir):
        return project_allclasses_list

    for filepath in os.listdir(module_project_libs_dir):
        if filepath.endswith('.jar'):
            project_allclasses_list += get_module_sourcecode_form_jar(module_project_libs_dir + filepath)
    return project_allclasses_list


def get_aarprefix_formapping(prefix, mapping_file_list):
    mapping_filename_list = []
    mapping_file_list = sorted(mapping_file_list, reverse=True)
    for mapping_file in mapping_file_list:
        origin_filepath = mapping_file.split('->')[0].strip()
        origin_filepath = origin_filepath.replace('.', '/')
        origin_filepath += '.class'
        mapping_filepath = mapping_file.split('->')[1].strip().replace('.', '/').replace(':', '.class')
        prefix = prefix.strip().replace('.', '/')
        if str.startswith(mapping_filepath, prefix):
            mapping_filename_list.append(mapping_filepath)

    return mapping_filename_list


def write_list_2file(arg_list, filename):
    pre = str(arg_list)
    pre = pre.replace(', ', '\n')
    pre = pre.replace('[', '')
    pre = pre.replace(']', '')
    pre = pre.replace('\'', '')
    pre = pre.replace('\\n', '')
    f = open(filename, "w")
    f.write(pre)
    f.close()


def parse_filepath(line):
    line = line.replace('\\r', '').replace('\\n', '')
    file_path = ''
    if len(line) > 0:
        lineslit = line.split()
        if len(lineslit) >= 1:
            file_path = lineslit[len(lineslit) - 1]
    return file_path


def get_release_classes(file_list, mapping_file_list):
    release_filename_list = []
    mapping_file_list = sorted(mapping_file_list, reverse=True)
    for mapping_file in mapping_file_list:
        origin_filepath = mapping_file.split('->')[0].strip()
        origin_filepath = origin_filepath.replace('.', '/')
        origin_filepath += '.class'
        mapping_filepath = mapping_file.split('->')[1].strip().replace('.', '/').replace(':', '.class')
        if origin_filepath in file_list:
            release_filename_list.append(mapping_filepath)

    return release_filename_list


def get_simple_mapping_list(filename):
    if not os.path.exists(filename):
        print('file not found: ' + filename)
        return

    mapping_file_list = []
    file_object = open(filename, 'rU')
    try:
        for line in file_object:
            if not line:
                break
            line = line.replace('\n', '').replace('\r', '')
            if line.find("->") >= 0 and line.endswith(":"):
                mapping_file_list.append(line)
    finally:
        file_object.close()

    return mapping_file_list


def parse_apk_detail(file_name):
    if not os.path.exists(base_config.apk_file_path):
        print('file not found: ' + base_config.apk_file_path)
        return

    proc = subprocess.Popen([base_config.aapt_file_path, 'l', '-v', base_config.apk_file_path], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    details = proc.stdout.readlines()
    f = open(file_name, 'w')
    f.writelines(details)
    f.close()


def write_classes_list_2file(arg_list, filename):
    pre = str(arg_list)
    pre = pre.replace(', ', "\n")
    pre = pre.replace('[', '')
    pre = pre.replace(']', '')
    pre = pre.replace('\'', '')
    pre = pre.replace('\r', '')
    f = open(filename, 'w')
    f.write(pre)
    f.close()

def save_maindexlist_2file():
    filename = base_config.app_package_path + 'TestClassForMainDex.class'
    f = open(base_config.maindexlist_file, 'w')
    f.write(filename)
    f.close()


def get_filesize(line):
    line = line.replace('\\r', '').replace('\\n', '')
    if len(line) > 0:
        valuelist = line.split()
        if len(valuelist) >= 2:
            size = float(valuelist[2])
            return size


def get_apk_file_ratio(txt_file_name):
    modules_file_list = []
    if not os.path.exists(txt_file_name):
        print('file not found: ' + txt_file_name)

    modules_origin_resfile_list = []
    get_filename_list(modules_origin_resfile_list, base_config.app_host_module_dir, base_config.host_module_name, True)
    modules_file_list.append(ModuleFile(base_config.dex_host_name))

    for sub_dex in base_config.sub_dex_list:
        get_filename_list(modules_origin_resfile_list, base_config.project_dir + sub_dex, sub_dex, False)
        modules_file_list.append(ModuleFile(sub_dex))

    modules_file_list.append(ModuleFile(base_config.android_sys))
    return parse_apk_file(txt_file_name,modules_file_list,modules_origin_resfile_list)


def parse_apk_file(txt_file_name,modules_file_list,modules_origin_resfile_list):
    file_object = open(txt_file_name, 'rU')
    try:
        for line in file_object:
            line = line.replace('\n', '')
            if line.find('.dex') >= 0:
                file_size = get_filesize(line)
                dex_file_arr = line.split('  ')
                dex_file_name = dex_file_arr[dex_file_arr.__len__() - 1]

                for module_file in modules_file_list:
                    if module_file.dex_name == dex_file_name.replace('.dex', ''):
                        module_file.dex_file_size = file_size

            if line.find('res/') >= 0 and not line.endswith('.apk') and not line == 'NoneType':
                file_size = get_filesize(line)
                res_name_list = line.split('  ')
                res_name = res_name_list[res_name_list.__len__() - 1]
                res_name = res_name.replace('-v4', '')
                if res_name.__contains__('res/'):
                    is_android_res = True
                    for res_file in modules_origin_resfile_list:
                        arr = str(res_file).split(' ')
                        if arr.__len__ > 1:
                            file_name = arr[arr.__len__() - 1]
                            dex_name = arr[0]
                            if res_name.__eq__(file_name):
                                is_android_res = False
                                for module_file in modules_file_list:
                                    if module_file.dex_name == dex_name:
                                        module_file.total_res_size = module_file.total_res_size + file_size
                                        break
                    if is_android_res:
                        for module_file in modules_file_list:
                            if module_file.dex_name == 'android_sys':
                                # print module_file.dex_name + ' ' + res_name + " " + str(file_size)
                                module_file.total_res_size = module_file.total_res_size + file_size
                                break
    finally:
        file_object.close()
    # for module_file in module_file_list:
    #     print module_file.dex_name + "  " + str(module_file.dex_file_size / 1024) + " res size: " + str(
    #         module_file.total_res_size / 1024)
    return modules_file_list


def module_file_list_init(txt_file_name):
    module_file_list = []
    if not os.path.exists(txt_file_name):
        print('file not found: ' + txt_file_name)
    total_module_file_list = []
    get_filename_list(total_module_file_list, base_config.app_host_module_dir, base_config.host_module_name, True)
    module_file_list.append(ModuleFile(base_config.dex_host_name))

    for sub_dex in base_config.sub_dex_list:
        get_filename_list(total_module_file_list, base_config.project_dir + sub_dex, sub_dex, False)
        module_file_list.append(ModuleFile(sub_dex))

    module_file_list.append(ModuleFile(base_config.android_sys))
    return module_file_list


def save_apkparse_result(module_file_list, file_path):
    if module_file_list.__len__ <= 0:
        return
    f = open(file_path, 'w')

    f.write('module_name'+ add_spaces('module_name')+'dex_name' + add_spaces('    ') +
            'dex_size'  + "        file_type       "  + 'file_size\n')
    f.write('-----------------------------------------------------------------------------------------\n')
    for module_file in module_file_list:

        pre = module_file.dex_name + add_spaces(module_file.dex_name)+ module_file.dex_name + ".dex" + add_spaces(module_file.dex_name) + str(
            round(module_file.dex_file_size / 1024, 1)) + "k            res             " + str(
            round(module_file.total_res_size / 1024, 1)) + 'k\n'
        f.write(pre)
    f.write('-----------------------------------------------------------------------------------------')
    f.close()


def add_spaces(str_content):
    space = ''
    num = 22 - len(str_content)
    i = 0
    while i < num:
        space = space + " "
        i = i + 1
    return space


def get_filename_list(file_list, rootpath, module_name, is_host_project):
    traverse_folder(rootpath, file_list, module_name, is_host_project)


def traverse_folder(rootpath, file_list, module_name, is_host_project):
    for file in os.listdir(rootpath):
        path = os.path.join(rootpath, file)
        if os.path.isfile(path) and path.__contains__('/res/') and not path.__contains__(
                '/res/values/') and not path.__contains__('.DS_Store'):
            module_name = base_config.dex_host_name if is_host_project else module_name
            filename = module_name + ' res/' + path.split('/res/')[1]
            # print filename
            file_list.append(filename)
        if os.path.isdir(path) and not path.__contains__('/build/'):
            traverse_folder(path, file_list, module_name, is_host_project)


class ModuleFile:
    dex_name = ''
    dex_file_size = 0
    total_res_size = 0

    def __init__(self, dex_name):
        self.dex_name = dex_name

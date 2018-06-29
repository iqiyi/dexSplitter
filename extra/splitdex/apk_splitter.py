import os,shutil,base_config,parse_util

def main():
    base_config.init()
    parse_util.gradle_clean()
    parse_util.gradle_assemble_release_withhack(False)

    if base_config.hack_para == 'hack_dx=true' and os.path.exists(base_config.hack_jar_file):
        shutil.copy(base_config.hack_jar_file, base_config.sdk_dx_path)

    simple_mapping_file_list = []
    subdex_classes_list = []

    if not os.path.exists(base_config.root_dir):
        os.makedirs(base_config.root_dir)
    print base_config.origin_mapping_file_path
    if not os.path.exists(base_config.origin_mapping_file_path):
        print('copy mapping file failed')
        return
    shutil.copy(base_config.origin_mapping_file_path, base_config.root_dir + base_config.tem_dir)

    print('get subdex_class_list begin')
    simple_mapping_file_list += parse_util.get_simple_mapping_list(base_config.copy_mapping_path)
    parse_util.write_list_2file(simple_mapping_file_list, base_config.temp_reduce_mappng_file)

    if not os.path.exists(base_config.temp_reduce_mappng_file) :
        print('get reduce mapping file failed')
        return

    subdex_classes_list.append('--subdex-start|' + base_config.dex_host_name)
    host_origin_classes = parse_util.get_host_project_classes()
    final_host_project_classes = parse_util.get_release_classes(host_origin_classes, simple_mapping_file_list);
    subdex_classes_list.append(final_host_project_classes)
    subdex_classes_list.append('--subdex-over|'+ base_config.dex_host_name)

    for sub_dex in base_config.sub_dex_list:
        subdex_classes_list.append('--subdex-start|'+sub_dex)
        module_sub_relative_path =  sub_dex
        tem_classes_list = parse_util.get_library_module_classes(module_sub_relative_path)
        module_sub_final_class_list = []
        module_sub_final_class_list += parse_util.get_release_classes(tem_classes_list, simple_mapping_file_list);
        subdex_classes_list.append(module_sub_final_class_list)
        subdex_classes_list.append('--subdex-over|'+sub_dex)

    subdex_classes_list.append('--subdex-start|'+base_config.android_sys)
    subdex_classes_list.append(parse_util.get_aarprefix_formapping('android.support', simple_mapping_file_list))
    subdex_classes_list.append(parse_util.get_aarprefix_formapping('android.arch', simple_mapping_file_list))
    subdex_classes_list.append('--subdex-over|'+base_config.android_sys)

    parse_util.write_classes_list_2file(subdex_classes_list, base_config.result_sub_list_file)
    shutil.copy(base_config.result_sub_list_file, base_config.app_host_module_dir)

    if not os.path.exists(base_config.result_sub_list_file):
        print('get subdex_class_list failed')

    print('get subdex_class_list end')

    parse_util.save_maindexlist_2file()
    shutil.copy(base_config.maindexlist_file, base_config.app_host_module_dir)
    print('get maindex_class_list end')

    parse_util.gradle_assemble_release_withhack(True)

    if base_config.hack_para == 'hack_dx=true':
        return

    parse_util.parse_apk_detail(base_config.temp_apk_detail_info_file)
    module_file_list = parse_util.get_apk_file_ratio(base_config.temp_apk_detail_info_file)
    parse_util.save_apkparse_result(module_file_list, base_config.apk_spliter_result)

    if not os.path.exists(base_config.apk_spliter_result):
        print('apk_ratio_file not exists')

    shutil.copy(base_config.apk_spliter_result, base_config.project_dir)


if __name__ == "__main__":
    main()
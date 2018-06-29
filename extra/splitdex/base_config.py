import os,ConfigParser

root_dir = os.path.dirname(os.path.realpath(__file__))
android_sys = 'android_sys'
apk_spliter_result = root_dir + '/outfiles/apk_splitter_result.txt'

def init():
    conf = ConfigParser.ConfigParser()
    conf.read('config.ini')

    global aapt_file_path
    global project_dir
    global app_package_path
    global hack_para
    global host_module_name
    global gradlew_path
    global origin_mapping_file_path
    global app_host_module_dir
    global tem_dir
    global copy_mapping_path
    global temp_jar_file
    global temp_reduce_mappng_file
    global library_module_source_jar_path
    global lib_endpath
    global result_sub_list_file
    global apk_file_path
    global temp_apk_detail_info_file
    global dex_host_name
    global sub_dex_list
    global hack_jar_file
    global sdk_dx_path
    global maindexlist_file

    aapt_file_path = conf.get('base_config', 'aapt_file_path')
    project_dir = conf.get('base_config', 'project_dir')
    app_package_path = conf.get('base_config', 'app_package_path')
    hack_para = conf.get('base_config', 'hack_para')
    host_module_name = conf.get('base_config', 'host_module_name')
    hack_jar_file = project_dir + conf.get('base_config', 'hack_jar_path')
    sdk_dx_path = conf.get('base_config', 'sdk_dx_path')

    dex_host_name = conf.get('sub_dex','moudle_host')
    sub_dex_list =  conf.get('sub_dex','moudle_sub').split('|')

    gradlew_path = project_dir + './gradlew'
    origin_mapping_file_path = project_dir + host_module_name + '/build/outputs/mapping/release/mapping.txt'
    app_host_module_dir = project_dir + host_module_name
    tem_dir = '/temp'
    copy_mapping_path = root_dir + tem_dir + '/mapping.txt'
    temp_jar_file = root_dir + tem_dir + '/temp_jar_file.txt'
    temp_reduce_mappng_file = root_dir + tem_dir + '/temp_reduce_mapping.txt'
    library_module_source_jar_path = "/build/intermediates/bundles/release/classes.jar"
    lib_endpath = "/libs/"
    result_sub_list_file = root_dir + '/outfiles/subdexeslist.txt'
    maindexlist_file = root_dir + '/outfiles/maindexlist.txt'
    apk_file_path = app_host_module_dir + '/build/outputs/apk/release/' + host_module_name + '-release-unsigned.apk'
    temp_apk_detail_info_file = root_dir + tem_dir + '/apk_detail_info.txt'




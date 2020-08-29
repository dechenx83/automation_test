# 欢迎
##《高效自动化测试平台开发实战》书籍配套代码

该REPO目前包含了书籍中的源码，作为书籍的补充，作者会不定期更新该REPO的代码，增加以及实现更多的功能。

代码部分分别对应了书中介绍的平台模块的主要介绍的功能模块，包括：

-配置管理 core.config
-测试资源管理 core.resource
-测试结果报告管理 core.result
-测试执行引擎 core.testengine

另外thridparty中包括了书中介绍的一些扩展测试方法的代码，比如Selenium封装，测试代码自动生成等。

## 使用方法

作者目前还在整理部分代码，希望能将该REPO打造成一个可安装的包，目前可能需要读者自行下载并且使用IDE来调试。

推荐IDE：PyCharm

步骤：
- Clone代码到本地
- 使用PyCharm打开目录，并且设置虚拟环境
- 安装requirement.txt中的依赖包
- userinterface目录中包括了命令行方式以及REST的启动方式

## Hello World
###一个基本的执行：
在example目录中有两个基本的演示文件：

    demo_list.testlist 包含了一个Hello World的测试用例 （测试列表章节）
    resource.json 一个资源配置文件 （资源配置章节）

**基本执行**

执行 userinterface下的start.py文件

$python3 start.py -s settingfile -t ../example/demo_list.testlist -r ../example/resource.json -u dechen
其中，-s settingfile指定了配置文件的路径，第一次执行会自动建立

如果一切正常，可以看到执行结果。

**日志路径**

默认情况下，可以看到settingfile目录中，产生了3个setting文件，可以在CaseRunnerSetting中看到，默认情况下的，框架日志路径，测试用例日志路径，以及测试用例配置的默认路径。3。


时间仓促，代码不免有bug，欢迎读者report issue。

如果读者有兴趣参与该项目，也可以和作者联系，提交PR。





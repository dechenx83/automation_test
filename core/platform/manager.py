from core.config.setting import static_setting
from core.resource.pool import ResourceSetting

static_setting.setting_path = "/Users/lilen/mySetting"
ResourceSetting.load()
print(f"资源文件路径{ResourceSetting.resource_path}")
print(f"配置文件路径{ResourceSetting.setting_path}")

ResourceSetting.resource_path = "/User/user/new_resource"
static_setting.save_all()



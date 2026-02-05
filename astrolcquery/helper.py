import yaml
import pathlib
from typing import Dict, Optional


class FieldHelper:
    _config_cache: Optional[Dict] = None

    @classmethod
    def _load_config(cls):
        if cls._config_cache is None:
            # 获取配置文件路径（假设在当前包的目录下）
            config_path = pathlib.Path(__file__).parent / "config" / "fields_schema.yaml"
            with open(config_path, "r", encoding="utf-8") as f:
                cls._config_cache = yaml.safe_load(f)
        return cls._config_cache

    @classmethod
    def get_info(cls, survey_name: str, field: str = None) -> str:
        config = cls._load_config()
        
        survey_name = survey_name.upper()
        global_info = config.get("GLOBAL", {})
        survey_info = config.get(survey_name, {})
        
        # 合并信息
        all_info = {**global_info, **survey_info}
        
        if field:
            return all_info.get(field, f"Field '{field}' is not defined for {survey_name}.")
        return all_info
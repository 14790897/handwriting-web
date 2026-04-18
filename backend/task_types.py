from typing import TypedDict, Literal, Union, Any, get_type_hints
from pydantic import BaseModel
import inspect

TaskStatus = Literal["pending", "processing", "completed", "failed"]


class GenerationTask(TypedDict, total=False):
    status: TaskStatus
    stage: str
    message: str
    progress: int
    created_at: float
    updated_at: float
    response_status_code: int
    response_content_type: str
    response_headers: dict
    response_body: bytes
    error_message: str


class GenerateHandwritingParams(BaseModel):
    """手写生成请求参数，文件和表单字段合一。"""
    # 表单字段
    text: str
    font_size: str
    line_spacing: str
    fill: str
    left_margin: str
    top_margin: str
    right_margin: str
    bottom_margin: str
    word_spacing: str
    line_spacing_sigma: str
    font_size_sigma: str
    word_spacing_sigma: str
    perturb_x_sigma: str
    perturb_y_sigma: str
    perturb_theta_sigma: str
    preview: str
    strikethrough_probability: str = "0"
    strikethrough_length_sigma: str = "0"
    strikethrough_width_sigma: str = "0"
    strikethrough_angle_sigma: str = "0"
    strikethrough_width: str = "0"
    ink_depth_sigma: str = "0"
    width: Union[str, None] = None
    height: Union[str, None] = None
    isUnderlined: str = "false"
    enableEnglishSpacing: str = "false"
    font_option: Union[str, None] = None
    pdf_save: str = "false"
    full_preview: str = "true"

    # 文件字段（非 Pydantic 验证，走 FastAPI File 绑定）
    # 注意：FastAPI 端点中仍需单独声明 File 参数，
    # 此字段仅作类型提示和文档用途


def form_dependency_from_model(model_cls: type[BaseModel]):
    """从 Pydantic BaseModel 自动生成 FastAPI Form 依赖注入函数。

    用法::

        @app.post("/api/xxx")
        async def xxx(params: MyModel = Depends(form_dependency_from_model(MyModel))):
            ...
    """
    from fastapi import Form

    # 提取字段名、类型、默认值
    fields: dict[str, Any] = {}
    hints = get_type_hints(model_cls, include_extras=True)
    for name, field_info in model_cls.model_fields.items():
        annotation = hints.get(name, str)
        if field_info.is_required():
            fields[name] = (annotation, Form(...))
        else:
            fields[name] = (annotation, Form(field_info.default))

    # 动态构建依赖函数签名
    def _as_form(**kwargs):
        return model_cls(**kwargs)

    sig = inspect.signature(_as_form)
    new_params = []
    for name, (annotation, default) in fields.items():
        new_params.append(inspect.Parameter(
            name,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=default,
            annotation=annotation,
        ))
    _as_form.__signature__ = sig.replace(parameters=new_params)
    return _as_form

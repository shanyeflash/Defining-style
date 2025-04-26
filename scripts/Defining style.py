import gradio as gr
from modules import scripts, shared, script_callbacks
import json
import os
import time
from functools import lru_cache

# 全局变量
stylespath = ""
categoriespath = os.path.join(scripts.basedir(), "categories.json")
image_folder = os.path.join(scripts.basedir(), "MGTV")
if not os.path.exists(image_folder):
    os.makedirs(image_folder)

# 初始化分类文件
if not os.path.exists(categoriespath):
    with open(categoriespath, 'w', encoding="utf-8") as f:
        json.dump({}, f, ensure_ascii=False, indent=2)

# 自定义CSS样式
custom_css = """
/* 分类按钮样式 */
.style-category-buttons {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 8px !important;
    margin-bottom: 10px !important;
}

.style-category-buttons label {
    background: #1E90FF !important;
    color: white !important;
    font-size: 14px !important;
    padding: 8px 16px !important;
    border-radius: 4px !important;
    border: 1px solid #1C86EE !important;
    transition: all 0.1s ease !important;
    min-width: 80px !important;
    text-align: center !important;
}

.style-category-buttons label:hover {
    background: #1C86EE !important;
    border-color: #1874CD !important;
}

.style-category-buttons input:checked + label {
    background: #104E8B !important;
    color: white !important;
    border-color: #104E8B !important;
}

/* 小按钮样式 */
.small-button {
    font-size: 14px !important;
    padding: 6px 12px !important;
    border-radius: 4px !important;
    background: var(--button-secondary-background-fill) !important;
    border: 1px solid var(--button-secondary-border-color) !important;
}

.small-button:hover {
    background: var(--button-secondary-background-fill-hover) !important;
}

/* 刷新按钮样式 */
.refresh-button {
    font-size: 16px !important;
    padding: 8px !important;
    border-radius: 4px !important;
    background: var(--button-secondary-background-fill) !important;
    position: absolute !important;
    top: 10px !important;
    right: 10px !important;
    width: 40px !important;
    height: 40px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* 反馈消息样式 */
.feedback-message {
    font-size: 14px !important;
    padding: 8px !important;
    border-radius: 4px !important;
    margin-top: 5px !important;
}

.feedback-message.success {
    background: var(--background-flash-success) !important;
    color: var(--text-color) !important;
}

.feedback-message.error {
    background: var(--background-flash-error) !important;
    color: var(--text-color) !important;
}

/* 主布局样式 */
#style_selector_main {
    background: var(--block-background-fill) !important;
    padding: 15px !important;
    border-radius: 8px !important;
    border: 1px solid var(--block-border-color) !important;
    margin-bottom: 15px !important;
    position: relative !important;
}

/* 折叠面板标题样式 */
.accordion > h3 {
    font-size: 16px !important;
    color: var(--block-label-text-color) !important;
    background: var(--block-background-fill) !important;
    padding: 10px !important;
    border-radius: 6px !important;
    border: 1px solid var(--block-border-color) !important;
    margin-bottom: 10px !important;
}

/* 输入框样式 */
#style_selector_main textarea, 
#style_selector_main input[type="text"] {
    background: var(--input-background-fill) !important;
    color: var(--input-text-color) !important;
    border-color: var(--input-border-color) !important;
}

/* 下拉菜单样式 */
#style_selector_main .gr-dropdown {
    background: var(--input-background-fill) !important;
    color: var(--input-text-color) !important;
    border-color: var(--input-border-color) !important;
}

/* 表情选择菜单样式 */
.emoji-dropdown {
    min-width: 150px !important;
    max-height: 200px !important;
    overflow-y: auto !important;
}

.emoji-button {
    font-size: 16px !important;
    padding: 4px 8px !important;
    min-width: 30px !important;
    margin: 2px !important;
}

.emoji-button:hover {
    background: var(--button-secondary-background-fill-hover) !important;
}
"""

# 表情符号列表
EMOJI_LIST = [
    "🧡", "💛", "💚", "💙", "💜", "🤎", "😀", "😁", "😊", "😇", 
    "🥰", "😍", "🤩", "😘", "😗", "☺️", "😚", "😙", "😋", "😛", 
    "😜", "🤪", "😝", "🤑", "🤗", "☕", "🍸", "🍹", "🍺", "🥂", 
    "🥤", "🧃", "🧉", "🧊", "👓", "🕶️", "🎸", "🎹", "📟", "🔋", 
    "🖥️", "💿", "📀", "🎞️", "📽️", "🎬", "📺", "📸", "🌟", "🌀", 
    "🌈", "🌂", "☂️", "☔", "⛱️", "⚡", "❄️", "⛄", "🔥", "💧", "🌊"
]

# 工具函数
@lru_cache(maxsize=2)
def get_json_content(file_path, _mtime=0):
    try:
        mtime = os.path.getmtime(file_path)
        if _mtime != mtime:
            get_json_content.cache_clear()
        with open(file_path, 'rt', encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        print(f"读取JSON文件错误: {str(e)}")
        return {}

def save_json_content(file_path, data):
    with open(file_path, 'w', encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    get_json_content.cache_clear()

def read_sdxl_styles(json_data, category):
    if not isinstance(json_data, list):
        return []
    names = [item['name'] for item in json_data if isinstance(item, dict) and 'name' in item and item.get('category') == category]
    names.sort()
    return names

def get_categories():
    categories_data = get_json_content(categoriespath)
    return [cat for cat in categories_data.keys() if cat != "全部"]

def getStyles(category):
    global stylespath
    json_path = os.path.join(scripts.basedir(), 'sdxl_styles.json')
    stylespath = json_path
    json_data = get_json_content(json_path)
    return read_sdxl_styles(json_data, category)

def createPositive(style, positive):
    json_data = get_json_content(stylespath)
    for template in json_data:
        if isinstance(template, dict) and template.get('name') == style:
            base_prompt = template.get('prompt', '')
            if positive and base_prompt:
                return f"{positive}, {base_prompt}"
            return base_prompt or positive
    return positive

def createNegative(style, negative):
    json_data = get_json_content(stylespath)
    for template in json_data:
        if isinstance(template, dict) and template.get('name') == style:
            json_negative = template.get('negative_prompt', '')
            return f"{json_negative}, {negative}" if json_negative and negative else json_negative or negative
    return negative

def add_style_with_feedback(style_name, positive_prompt, negative_prompt, image, category):
    json_data = get_json_content(stylespath)
    existing_names = [item['name'] for item in json_data if isinstance(item, dict) and 'name' in item]
    if style_name in existing_names:
        return gr.update(choices=getStyles(category)), "❌ 样式名称已存在!", "error"
    if not style_name.strip():
        return gr.update(choices=getStyles(category)), "❌ 样式名称不能为空!", "error"

    new_style = {
        "name": style_name,
        "prompt": positive_prompt,
        "negative_prompt": negative_prompt,
        "category": category
    }
    if image:
        image_path = os.path.join(image_folder, f"{style_name}.png")
        image.save(image_path)
        new_style["image"] = image_path

    json_data.append(new_style)
    save_json_content(stylespath, json_data)

    categories_data = get_json_content(categoriespath)
    if category not in categories_data:
        categories_data[category] = []
    if style_name not in categories_data[category]:
        categories_data[category].append(style_name)
    save_json_content(categoriespath, categories_data)

    time.sleep(0.3)
    return gr.update(choices=getStyles(category)), "✅ 样式添加成功!", "success"

def modify_style_with_feedback(style_name, positive_prompt, negative_prompt, image, category):
    json_data = get_json_content(stylespath)
    modified = False

    for template in json_data:
        if template['name'] == style_name:
            old_category = template.get('category', '')
            template['prompt'] = positive_prompt
            template['negative_prompt'] = negative_prompt
            template['category'] = category
            if image:
                image_path = os.path.join(image_folder, f"{style_name}.png")
                image.save(image_path)
                template["image"] = image_path
            modified = True

            categories_data = get_json_content(categoriespath)
            if old_category in categories_data and style_name in categories_data[old_category]:
                categories_data[old_category].remove(style_name)
            if category not in categories_data:
                categories_data[category] = []
            if style_name not in categories_data[category]:
                categories_data[category].append(style_name)
            save_json_content(categoriespath, categories_data)
            break

    if modified:
        save_json_content(stylespath, json_data)
        time.sleep(0.3)
        return gr.update(choices=getStyles(category)), "✅ 样式更新成功!", "success"
    return gr.update(choices=getStyles(category)), "❌ 未找到样式!", "error"

def delete_style_with_feedback(style_name, category):
    json_data = get_json_content(stylespath)
    new_json_data = [t for t in json_data if t['name'] != style_name]

    if len(new_json_data) < len(json_data):
        image_path = os.path.join(image_folder, f"{style_name}.png")
        if os.path.exists(image_path):
            os.remove(image_path)

        save_json_content(stylespath, new_json_data)

        categories_data = get_json_content(categoriespath)
        if category in categories_data and style_name in categories_data[category]:
            categories_data[category].remove(style_name)
        save_json_content(categoriespath, categories_data)

        time.sleep(0.3)
        return gr.update(choices=getStyles(category)), "✅ 样式删除成功!", "success"
    return gr.update(choices=getStyles(category)), "❌ 未找到样式!", "error"

def get_style_image(style):
    json_data = get_json_content(stylespath)
    for template in json_data:
        if template['name'] == style and 'image' in template:
            return template['image']
    return None

def get_style_details(style):
    json_data = get_json_content(stylespath)
    for template in json_data:
        if template['name'] == style:
            return template.get('name', ''), template.get('prompt', ''), template.get('negative_prompt', ''), template.get('category', '')
    return "", "", "", ""

def add_category(category_name, emoji):
    if not category_name.strip():
        return False, "❌ 分类名称不能为空!", "error"
    categories_data = get_json_content(categoriespath)
    final_name = f"{emoji} {category_name}" if emoji else category_name
    if final_name not in categories_data:
        categories_data[final_name] = []
        save_json_content(categoriespath, categories_data)
        return True, "✅ 分类添加成功!", "success"
    return False, "❌ 分类已存在!", "error"

def rename_category(old_name, new_name):
    if not new_name.strip():
        return False, "❌ 新分类名称不能为空!", "error"
    if old_name == new_name:
        return False, "❌ 新分类名称与原名称相同!", "error"
    
    categories_data = get_json_content(categoriespath)
    if old_name not in categories_data:
        return False, "❌ 原分类不存在!", "error"
    if new_name in categories_data:
        return False, "❌ 新分类名称已存在!", "error"
    
    # 更新分类数据
    categories_data[new_name] = categories_data.pop(old_name)
    save_json_content(categoriespath, categories_data)
    
    # 更新样式数据中的分类名称
    json_data = get_json_content(stylespath)
    for style in json_data:
        if style.get('category') == old_name:
            style['category'] = new_name
    save_json_content(stylespath, json_data)
    
    return True, "✅ 分类重命名成功!", "success"

def delete_category(category_name):
    categories_data = get_json_content(categoriespath)
    if category_name in categories_data:
        del categories_data[category_name]
        save_json_content(categoriespath, categories_data)

        json_data = get_json_content(stylespath)
        for style in json_data:
            if style.get('category') == category_name:
                style['category'] = ""
        save_json_content(stylespath, json_data)

        return True, "✅ 分类删除成功!", "success"
    return False, "❌ 未找到分类!", "error"

class StyleSelectorXL(scripts.Script):
    def __init__(self):
        super().__init__()
        self.styleNames = []
        self.boxx = None
        self.boxxIMG = None
        self.neg_prompt_boxTXT = None
        self.neg_prompt_boxIMG = None
        self.current_category = ""

    def title(self):
        return "🎨 样式选择器"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        gr.HTML(f"<style>{custom_css}</style>")

        categories = get_categories()
        self.current_category = categories[0] if categories else ""
        self.styleNames = getStyles(self.current_category)
        enabled = False  # 默认禁用

        with gr.Group(elem_id="style_selector_main"):
            with gr.Accordion("🎨 样式选择器", open=enabled):
                is_enabled = gr.Checkbox(
                    value=enabled,
                    label="启用样式选择器",
                    elem_id="style_selector_enabled"
                )

                refresh_btn = gr.Button(
                    "🔄",
                    variant="secondary",
                    elem_classes=["refresh-button"],
                    title="刷新"
                )

                with gr.Row(variant="panel"):
                    category_radio = gr.Radio(
                        choices=categories,
                        value=self.current_category,
                        label="分类",
                        interactive=True,
                        elem_id="style_category_radio",
                        elem_classes=["style-category-buttons"]
                    )

                with gr.Group():
                    style = gr.Radio(
                        label='选择样式',
                        choices=self.styleNames,
                        value=self.styleNames[0] if self.styleNames else None,
                        interactive=True
                    )

                    style_image_display = gr.Image(
                        type="filepath",
                        label="样式预览",
                        height=180,
                        interactive=False
                    )

                    with gr.Row(variant="compact"):
                        send_to_prompt_btn = gr.Button("应用到提示词", variant="primary")
                        del_up_btn = gr.Button("清空正向提示", variant="secondary")
                        del_dn_btn = gr.Button("清空反向提示", variant="secondary")

                with gr.Accordion("📁 分类管理", open=False):
                    with gr.Row(variant="compact"):
                        emoji_dropdown = gr.Dropdown(
                            choices=EMOJI_LIST,
                            label="选择表情",
                            elem_classes=["emoji-dropdown"]
                        )
                        new_category_name = gr.Textbox(label="分类名称", placeholder="输入分类名称")
                    with gr.Row(variant="compact"):
                        add_category_btn = gr.Button("添加分类", variant="secondary", elem_classes=["small-button"])
                        delete_category_btn = gr.Button("删除分类", variant="secondary", elem_classes=["small-button"])
                        rename_category_btn = gr.Button("分类改名", variant="secondary", elem_classes=["small-button"])
                    category_feedback = gr.Textbox(
                        label="状态",
                        interactive=False,
                        elem_classes=["feedback-message"]
                    )

                with gr.Accordion("🛠️ 样式管理", open=False):
                    with gr.Row():
                        with gr.Column(scale=2):
                            new_name = gr.Textbox(label="样式名称", placeholder="输入样式名称")
                            new_positive = gr.Textbox(
                                label="正向提示词",
                                placeholder="使用{prompt}作为占位符",
                                lines=3
                            )
                            new_negative = gr.Textbox(
                                label="反向提示词",
                                placeholder="输入不需要的元素",
                                lines=3
                            )
                            style_category = gr.Dropdown(
                                choices=categories,
                                value=self.current_category,
                                label="分类"
                            )
                        with gr.Column(scale=1):
                            new_image = gr.Image(
                                type="pil",
                                label="上传预览图",
                                height=180
                            )

                    with gr.Row(variant="compact"):
                        extract_style_btn = gr.Button("提取样式提示", variant="secondary")
                        extract_gen_btn = gr.Button("提取生图提示", variant="secondary")
                        modify_btn = gr.Button("更新", variant="primary")
                        add_btn = gr.Button("添加", variant="primary")
                        delete_btn = gr.Button("删除", variant="secondary")

                    feedback_message = gr.Textbox(
                        label="状态",
                        interactive=False,
                        elem_classes=["feedback-message"]
                    )

        positive_box = self.boxxIMG if is_img2img else self.boxx
        negative_box = self.neg_prompt_boxIMG if is_img2img else self.neg_prompt_boxTXT

        def update_style_choices(category):
            return gr.update(choices=getStyles(category))

        def extract_generation_prompts(positive, negative):
            return positive, negative, "✅ 生图提示已提取!", "success"

        style.change(
            fn=get_style_image,
            inputs=[style],
            outputs=[style_image_display]
        )

        category_radio.change(
            fn=update_style_choices,
            inputs=[category_radio],
            outputs=[style]
        ).then(
            fn=lambda cat: cat,
            inputs=[category_radio],
            outputs=[category_radio]
        )

        refresh_btn.click(
            fn=lambda cat: [gr.update(choices=getStyles(cat)), "🔄 样式已刷新!", "success"],
            inputs=[category_radio],
            outputs=[style, feedback_message, feedback_message]
        )

        send_to_prompt_btn.click(
            fn=lambda s, pp, np: [
                createPositive(s, pp),
                createNegative(s, np),
                "✅ 提示词已应用!",
                "success"
            ],
            inputs=[style, positive_box, negative_box],
            outputs=[positive_box, negative_box, feedback_message, feedback_message]
        )

        del_up_btn.click(
            fn=lambda: ["", "✅ 正向提示已清空!", "success"],
            inputs=[],
            outputs=[positive_box, feedback_message, feedback_message]
        )

        del_dn_btn.click(
            fn=lambda: ["", "✅ 反向提示已清空!", "success"],
            inputs=[],
            outputs=[negative_box, feedback_message, feedback_message]
        )

        extract_style_btn.click(
            fn=get_style_details,
            inputs=[style],
            outputs=[new_name, new_positive, new_negative, style_category]
        )

        extract_gen_btn.click(
            fn=extract_generation_prompts,
            inputs=[positive_box, negative_box],
            outputs=[new_positive, new_negative, feedback_message, feedback_message]
        )

        add_btn.click(
            fn=add_style_with_feedback,
            inputs=[new_name, new_positive, new_negative, new_image, style_category],
            outputs=[style, feedback_message, feedback_message]
        )

        modify_btn.click(
            fn=modify_style_with_feedback,
            inputs=[style, new_positive, new_negative, new_image, style_category],
            outputs=[style, feedback_message, feedback_message]
        )

        delete_btn.click(
            fn=delete_style_with_feedback,
            inputs=[style, category_radio],
            outputs=[style, feedback_message, feedback_message]
        )

        add_category_btn.click(
            fn=add_category,
            inputs=[new_category_name, emoji_dropdown],
            outputs=[category_feedback, category_feedback]
        ).then(
            fn=lambda: [gr.update(choices=get_categories()), gr.update(choices=get_categories())],
            inputs=[],
            outputs=[category_radio, style_category]
        )

        delete_category_btn.click(
            fn=delete_category,
            inputs=[category_radio],
            outputs=[category_feedback, category_feedback]
        ).then(
            fn=lambda: [gr.update(choices=get_categories()), gr.update(choices=get_categories())],
            inputs=[],
            outputs=[category_radio, style_category]
        )

        rename_category_btn.click(
            fn=lambda old_name, new_name: rename_category(old_name, new_name),
            inputs=[category_radio, new_category_name],
            outputs=[category_feedback, category_feedback]
        ).then(
            fn=lambda: [gr.update(choices=get_categories()), gr.update(choices=get_categories())],
            inputs=[],
            outputs=[category_radio, style_category]
        )

        return [is_enabled, style]

    def process(self, p, is_enabled, style):
        if not is_enabled or not style:
            return

        for i, prompt in enumerate(p.all_prompts):
            p.all_prompts[i] = createPositive(style, prompt)

        for i, prompt in enumerate(p.all_negative_prompts):
            p.all_negative_prompts[i] = createNegative(style, prompt)

        p.extra_generation_params["样式选择器启用"] = True
        p.extra_generation_params["样式选择器样式"] = style

    def after_component(self, component, **kwargs):
        if kwargs.get("elem_id") == "txt2img_prompt":
            self.boxx = component
        if kwargs.get("elem_id") == "img2img_prompt":
            self.boxxIMG = component
        if kwargs.get("elem_id") == "txt2img_neg_prompt":
            self.neg_prompt_boxTXT = component
        if kwargs.get("elem_id") == "img2img_neg_prompt":
            self.neg_prompt_boxIMG = component
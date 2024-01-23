import requests
import re
import itemdb
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import os
import subprocess
import shutil
import time



Url_list = []
# Item_list = []
Item_tag_data = {}

Gd_installed_path = ""
Target_text_file = ""

Tag_item_file = ""
Tag_gdx1_item_file = ""
Tag_gdx2_item_file = ""

root = tk.Tk()
root.title("恐怖黎明bd导入助手")

def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"文件夹 {path} 创建成功")
    else:
        print(f"文件夹 {path} 已经存在")

def delete_if_exists(path):
    if os.path.exists(path):
        if os.path.isfile(path):
            os.remove(path)  # remove the file
        elif os.path.isdir(path):
            shutil.rmtree(path)  # remove dir and all contains
        print(f'Path {path} has been removed.')
    else:
        print(f'Path {path} does not exist.')

def open_directory_dialog():
    directory = filedialog.askdirectory()
    file_entry_gd_install.delete(0, tk.END)
    file_entry_gd_install.insert(0, directory)

def open_file_dialog():
    directory = filedialog.askopenfilename()
    file_entry_text_path.delete(0, tk.END)
    file_entry_text_path.insert(0, directory)

def execute_command(command):
    subprocess.Popen(command, shell=True)

def execute_script():
    if messagebox.askyesno("确认", "确定要导入这些build吗？"):
        global Gd_installed_path,Url_list,Target_text_file
        Gd_installed_path = file_entry_gd_install.get()
        text_file  = file_entry_text_path.get()
        if text_file == "":
            Target_text_file = Gd_installed_path + "/resources/Text_ZH.arc"
        else:
            Target_text_file = text_file
        text = text_entry.get("1.0", tk.END)
        url_list = text.split('\n')
        Url_list = url_list
        success = unpack_arc()
        if success == False:
            return
        success = get_item()
        if success == False:
            return
        success = process_Item_tag_data()
        if success == False:
            return
        messagebox.showinfo("完成", "导入完成")


def unpack_arc():
    # 判断是否存在setting文件夹
    global Gd_installed_path,Tag_gdx1_item_file,Tag_gdx2_item_file,Tag_item_file
    path = Gd_installed_path + "/settings"
    create_directory(path)
    delete_if_exists(path+"/text_zh")
    command = [Gd_installed_path+"/ArchiveTool.exe", Target_text_file ,'-extract' ,path]
    p = subprocess.Popen(command, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    print("正在解压汉化包......")
    if p.returncode != 0:
        messagebox.showerror("错误", "解包汉化包失败。\n请检查1.游戏是否正在运行，请关闭游戏后重试;2.游戏根目录是否选择正确。")
        return False
    # path = path.replace("/","\\")
    Tag_item_file = path + "/text_zh/tags_items.txt"
    Tag_gdx1_item_file = path + "/text_zh/aom/tagsgdx1_items.txt"
    Tag_gdx2_item_file = path + "/text_zh/fg/tagsgdx2_items.txt"
    return True


def get_item():
    #循环请求用户输入要爬取的项，并保存到item_list中
    for url in Url_list:
        try:
            if url == "":
                continue
            response = requests.get(url)
            response.encoding = "utf-8"
            html = response.text
            #提取html响应中，所有形如"item":"it11737"中it11737的部份，使用正则
            print("正在爬取grimtools网站bd信息......当前处理："+url)
            items = re.findall('"item":"(.*?)"', html)
            item_with_fix = []
            for item in items:
                content = re.findall(item+'"(.*?)\}',html)
                prefix = re.findall('"prefix":"(.*?)"',content[0])
                suffix = re.findall('"suffix":"(.*?)"',content[0])
                item =  item + ":" + str(prefix) + "," + str(suffix)
                item_with_fix.append(item)
            success = get_item_tag(item_with_fix)
            if success == False:
                print("当前bd导入失败："+url)
                messagebox.showinfo("提示", "当前bd导入失败："+url)
            # item_list.extend(item_with_fix)
            time.sleep(0.5) #增加延迟防止频繁请求
        except:
            messagebox.showerror("错误", "爬取失败，请检查网络连接。")
            return False
    return True


def get_gix_name(fix_id):
    # print(fix_id)
    try:
        fix_content = re.findall(fix_id+':\{(.*?)\}',itemdb.fixes)
        fix_tag = re.findall('c:"(.*?)"',fix_content[0])
        translate_name = re.findall('"'+fix_tag[0]+'":"(.*?)"',itemdb.translate)
        return translate_name[0]
    except:
        print(fix_id+" 解析失败")
        return 0

def get_item_tag(item_list):
    #去重
    print("正在从数据库中查询bd包含的物品信息......")
    for item in item_list:
        try:
            fix = item.split(":")[1]
            item = item.split(":")[0]
            item_content = re.findall(item+':\{(.*?)\}',itemdb.allItem)
            itemTag = re.findall('a:"(.*?)"',item_content[0])
            if itemTag==[]:
                itemTag = re.findall('d:"(.*?)"',item_content[0])
            if itemTag != []:
                itemTag = itemTag[0]
                if "'" in fix :
                    fixs = re.findall("'(.*?)'",fix)
                    fix_name = ""
                    for fix in fixs:
                        fix_name_tmp = get_gix_name(fix)
                        if fix_name_tmp != 0:
                            fix_name += fix_name_tmp+"、"                       
                else:
                    fix_name = ""
                if itemTag in Item_tag_data:
                    for fix in fix_name.split("、"):
                        if fix not in Item_tag_data[itemTag]:
                            Item_tag_data[itemTag] = Item_tag_data[itemTag] + fix_name
                else:
                    Item_tag_data[itemTag] = fix_name
            else:
                messagebox.showinfo("未找到物品",item+"未找到")
        except:
            messagebox.showerror("错误",item+" 解析失败\n请检查导入的bd是否为1.2.0.3版本bd，暂不支持其它版本。")
            return False
    return True

def process_Item_tag_data():
    print("正在处理汉化文件......")
    for item_tag,item_fix in Item_tag_data.items():
        try:
            if "GDX1" in item_tag:
                f = open(Tag_gdx1_item_file,"r",encoding='utf-8')
            elif "GDX2" in item_tag:
                f = open(Tag_gdx2_item_file,"r",encoding='utf-8')
            else:
                f = open(Tag_item_file,"r",encoding='utf-8')
            content = f.read()
            item_name = re.findall(item_tag+"=(.*?)\n",content)
            if item_name != []:
                print("当前处理："+item_tag+"："+item_name[0]+"["+item_fix+"]")
                if item_fix != "":
                    if item_tag+"Desc" in content or item_tag+"_Desc" in content:
                        # pass
                        item_fix_name = re.findall(item_tag+"[_]*Desc=(.*?)\n",content)
                        content = content.replace(item_fix_name[0],item_fix_name[0]+"^w^n(推荐词缀：)"+item_fix.strip("、"))
                    else:
                        # pass
                        content = content.replace(item_name[0],item_name[0]+"\n"+item_tag+"Desc=^w^n(推荐词缀：)"+item_fix.strip("、")+"\n")
                content = content.replace(item_name[0],"^r☆☆☆"+item_name[0]+"^r☆☆☆")
            else:
                print(item_tag+" not found!!!")
            f.close()
            # print(content)
            if "GDX1" in item_tag:
                f = open(Tag_gdx1_item_file,"w",encoding='utf-8')
            elif "GDX2" in item_tag:
                f = open(Tag_gdx2_item_file,"w",encoding='utf-8')
            else:
                f = open(Tag_item_file,"w",encoding='utf-8')
            f.write(content)
            f.close()
        except:
            messagebox.showerror("错误","文件写入失败，请检查文件读写权限")
            return False
    return True

if __name__ == '__main__':
    # 文字说明
    description_label_info = tk.Label(root, text="本助手可以导入GDtools网站bd中的物品信息到汉化包中，并做特殊标记，方便萌新（作者本人）保留装备。\n暂仅支持1.2.0.3版本，需要选择GD安装路径。建议关闭游戏防止文件占用问题。\n原理为解压汉化包到游戏目录的setting路径下，因setting路径下汉化优先级较高，可以在游戏内覆盖原汉化.\n如无需使用时，可直接删除setting目录下的text_zh目录，会自动恢复为原汉化包")
    description_label_info.grid(row=0, column=0, columnspan=2)
    
    # 文字说明
    description_label_gd_install = tk.Label(root, text="请选择GD的安装文件夹，如C:\Program Files (x86)\Steam\steamapps\common\Grim Dawn")
    description_label_gd_install.grid(row=1, column=0, columnspan=2)

    # 文件输入栏
    file_entry_gd_install = tk.Entry(root)
    file_entry_gd_install.grid(row=2, column=0, sticky="ew")

    # 打开文件夹对话框的按钮
    open_directory_button_gd_install = tk.Button(root, text="打开文件夹", command=open_directory_dialog)
    open_directory_button_gd_install.grid(row=2, column=1)

    # 文字说明
    description_label_text_path = tk.Label(root, text="可选：选择GD的汉化包文件位置，可复制原汉化包放在桌面，如Text_zh.arc，使用后可删除。\n可留空，默认导入游戏根目录下/resources/Text_ZH.arc文件。")
    description_label_text_path.grid(row=3, column=0, columnspan=2)

    # 文件输入栏
    file_entry_text_path = tk.Entry(root)
    file_entry_text_path.grid(row=4, column=0, sticky="ew")

    # 打开文件对话框的按钮
    open_file_button = tk.Button(root, text="打开文件", command=open_file_dialog)
    open_file_button.grid(row=4, column=1)

    # 文字说明
    description_label = tk.Label(root, text="请在下方输入grim tools中build的网址，如https://www.grimtools.com/calc/XXXXXXXX\n可以多个，每行一个，暂仅支持1.2.0.3版本bd，其他版本可能出现问题。")
    description_label.grid(row=5, column=0, columnspan=2)

    # 文本输入框
    text_entry = ScrolledText(root)
    text_entry.grid(row=6, column=0, columnspan=2, sticky="ew")

    # 执行脚本的按钮
    execute_button = tk.Button(root, text="执行脚本", command=execute_script)
    execute_button.grid(row=7, column=0, columnspan=2)

    root.grid_columnconfigure(0, weight=1)  # 使得第一列可以自动扩展

    root.mainloop()




import re
import os
import traceback
import sys
import uuid
import zipfile
from datetime import datetime
import sys
import io
import html
import urllib.request
import json
import subprocess
import time
import concurrent.futures

CURRENT_VERSION = "1.0.2"
GITHUB_USER = "hikikomori1870-bit"
GITHUB_REPO = "clean-truyen-hehe"
VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.json"

def check_for_updates():
    print(f"\n🔍 Đang kiểm tra bản cập nhật... (Phiên bản hiện tại: {CURRENT_VERSION})")
    try:
        with urllib.request.urlopen(VERSION_URL, timeout=5) as response:
            data = json.loads(response.read().decode())
            latest_version = data.get("version")
            download_url = data.get("download_url")
            changelog = data.get("changelog", "")
        if latest_version and latest_version != CURRENT_VERSION:
            print(f"\n🚀 PHÁT HIỆN BẢN CẬP NHẬT MỚI: {latest_version}")
            print(f"📝 Nội dung thay đổi: {changelog}")
            choice = input("👉 Bạn có muốn cập nhật ngay không? (y/n): ").strip().lower()            
            if choice == 'y':
                print("⏳ Đang tải xuống bản mới...")
                current_exe = sys.executable
                new_exe = current_exe + ".new"
                urllib.request.urlretrieve(download_url, new_exe)
                print("✅ Tải xong! Đang cài đặt...")
                batch_script = f"""
@echo off
timeout /t 2 /nobreak > NUL
del "{current_exe}"
move "{new_exe}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
"""
                batch_file = "update_tool.bat"
                with open(batch_file, "w") as f:
                    f.write(batch_script)
                subprocess.Popen(batch_file, shell=True)
                sys.exit(0)
        else:
            print("✅ Bạn đang dùng phiên bản mới nhất.")
            time.sleep(1)
    except Exception as e:
        print(f"⚠️ Không thể kiểm tra cập nhật: {e}")
        print("   (Bỏ qua và tiếp tục chạy chương trình...)")
        time.sleep(1)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
INDENT_STYLE = "\u3000\u3000" 
REPLACEMENT_CONFIG_FILE = "replacements.txt"
GARBAGE_CONFIG_FILE = "garbage.txt" 
def fast_print(*args, **kwargs):
    kwargs['flush'] = True
    print(*args, **kwargs)
def log_error(file_name, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open("processing_errors.log", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {file_name}: {message}\n")
    except: pass
def load_garbage_patterns():
    patterns = [
        r'https?://\S+', r'www\.\S+', r'\w+\.com', r'\w+\.net',
        r'Sưu tầm bởi.*?', r'Chúc bạn đọc truyện vui vẻ'
    ]
    if os.path.exists(GARBAGE_CONFIG_FILE):
        try:
            with open(GARBAGE_CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    if line.strip(): patterns.append(line.strip())
        except: pass
    return patterns
def clean_garbage_text(text, patterns=None):
    if patterns is None:
        patterns = load_garbage_patterns()
    for pattern in patterns:
        try:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        except: pass
    return text
def normalize_punctuation(text):
    text = re.sub(r'\s+([,.:;?!])', r'\1', text)
    text = re.sub(r'([,.:;?!])(?=[^\s\d])', r'\1 ', text)
    text = re.sub(r' +', ' ', text)
    return text
def load_replacements():
    replace_dict = {}
    if os.path.exists(REPLACEMENT_CONFIG_FILE):
        try:
            with open(REPLACEMENT_CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    if '=' in line:
                        parts = line.strip().split('=')
                        if len(parts) >= 2:
                            replace_dict[parts[0].strip()] = parts[1].strip()
        except: pass
    return replace_dict
def cn_to_int(cn_str):
    cn_map = {
        '〇': 0, '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, 
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10, '百': 100, '千': 1000, '万': 10000,
        '0': 0, '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9
    }    
    if not cn_str: return 0
    if str(cn_str).isdigit(): return int(cn_str)
    result = 0
    temp = 0
    temp_unit = 1    
    try:
        for char in str(cn_str):
            if char in cn_map:
                val = cn_map[char]
                if val >= 10:
                    if val > temp_unit:
                        temp_unit = val
                        if temp == 0: temp = 1
                        result += temp * val
                        temp = 0
                    else:
                        temp_unit = val
                        result += val
                else:
                    temp = val
        result += temp
        return result
    except: return 0
def sanitize_filename(name):
    clean = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    return clean[:100]
def clean_common_entities(text):
    text = html.unescape(text)
    text = text.replace("&nbsp;", " ")
    return text
def apply_replacements(text, replace_dict):
    for old, new in replace_dict.items():
        text = text.replace(old, new)
    return text
def clean_chapter_title(line, current_index):
    final_text = line.strip()
    final_text = clean_common_entities(final_text)    
    pattern = r'^(番外|第\s*[0-9一二三四五六七八九十百千万\s]+\s*[章卷]|Quyển\s*[0-9一二三四五六七八九十百千万\d]+|Chương\s*\d+|Chapter\s*\d+|Hồi\s*\d+|分卷阅读\s*\d*|^\d+[\s\.\-、]*)'                 
    text = final_text
    if len(final_text) > 3 and not final_text.isdigit():
        text = re.sub(pattern, '', final_text, flags=re.IGNORECASE)        
    text = text.strip(" -=—–─_*　：:,，.、")        
    if "番外" in final_text and "番外" not in text:
        text = "番外 " + text       
    return text if text else f"第{current_index}章"
def check_sequence_gaps(raw_chapter_titles):
    print(f"\n{'*'*20} KIỂM TRA LỖI ĐÁNH SỐ CỦA TÁC GIẢ {'*'*20}")
    last_num = None
    has_gap = False   
    num_pattern = re.compile(r'(?:第\s*([0-9一二三四五六七八九十百千万]+)\s*[章回]|Chương\s*(\d+)|^\s*(\d+))', re.IGNORECASE)
    for raw_title in raw_chapter_titles:
        match = num_pattern.search(raw_title)
        if match:
            val_str = match.group(1) or match.group(2) or match.group(3)
            current_num = cn_to_int(val_str)            
            if last_num is not None:
                if current_num > last_num + 1:
                    print(f"❌ PHÁT HIỆN THIẾU CHƯƠNG: Tác giả viết từ [{last_num}] nhảy vọt lên [{current_num}]")
                    print(f"   -> Dòng lỗi trong file: \"{raw_title}\"")
                    has_gap = True
                elif current_num < last_num:
                    print(f"⚠️ CẢNH BÁO: Số chương bị lùi hoặc trùng: [{last_num}] xuống [{current_num}]")
                    print(f"   -> Dòng nghi vấn: \"{raw_title}\"")
                    has_gap = True            
            last_num = current_num            
    if not has_gap:
        print("✅ Chúc mừng: Tác giả của bợn đánh số chương chuẩn vl, không thấy đứt đoạn.")
    else:
        print(f"\n❗ Lưu ý: Bạn nên kiểm tra lại file gốc tại các vị trí báo lỗi trên.")
    print(f"{'*'*65}\n")
def interactive_check_chapters(chapters, is_silent=False):
    print(f"\n{'='*20} RÀ SOÁT CHƯƠNG NGẮN/LỖI {'='*20}")
    refined_chapters = []
    i = 0    
    history_stack = [] 
    while i < len(chapters):
        current_title, current_lines = chapters[i]
        content_text = "".join(map(str, current_lines[1:]))
        char_count = len(content_text.strip())        
        is_short_chapter = (i > 0 and char_count < 200)        
        if is_short_chapter:
            if is_silent:
                if char_count < 50:
                    if refined_chapters:
                        prev_title, prev_lines = refined_chapters[-1]
                        prev_lines.extend(current_lines)
                        print(f"🤖 [Auto] Gộp chương siêu ngắn '{current_title}' ({char_count} chars) vào chương trước.")
                    else:
                        refined_chapters.append((current_title, current_lines))
                else:
                    refined_chapters.append((current_title, current_lines))
                    print(f"🤖 [Auto] Giữ chương ngắn '{current_title}' ({char_count} chars).")
                i += 1
            else:
                current_state_snapshot = [
                    (t, list(l)) for t, l in refined_chapters
                ]                
                print(f"{'!'*10} PHÁT HIỆN CHƯƠNG NGHI VẤN {'!'*10}")
                print(f"🔖 Tiêu đề: {current_title}") 
                print(f"📉 Độ dài: {char_count} ký tự")
                print(f"📄 Trích đoạn:\n{'-'*30}")
                print('\n'.join([str(l).strip() for l in current_lines[:6] if str(l).strip()]))
                print(f"{'-'*30}")            
                print("👉 Chọn cách xử lý:")
                print("   [1] GỘP vào chương trước (Giữ nguyên toàn bộ nội dung)")
                print("   [2] GIỮ NGUYÊN (Để thành chương riêng)")
                print("   [3] XÓA BỎ (Nếu là rác)")
                print("   [b] QUAY LẠI (Undo quyết định trước đó)")                
                choice = input("   Nhập lựa chọn (Enter=1, b=Back): ").strip()                
                if choice.lower() == 'b':
                    if not history_stack:
                        print("⚠️ Không thể quay lại xa hơn (Đây là chương đầu tiên hoặc chưa có lịch sử)!")
                        continue 
                    else:
                        last_i, last_refined_chapters = history_stack.pop()
                        i = last_i
                        refined_chapters = last_refined_chapters
                        print("⏪ Đã quay lại quyết định trước đó.")
                        continue
                history_stack.append((i, current_state_snapshot))
                if choice == '2':
                    refined_chapters.append((current_title, current_lines))
                elif choice == '3':
                    print("🗑️ Đã xóa.\n")
                else:
                    if refined_chapters:
                        prev_title, prev_lines = refined_chapters[-1]
                        prev_lines.extend(current_lines) 
                        print(f"🔗 Đã gộp thành công.\n")
                    else:
                        refined_chapters.append((current_title, current_lines))                
                i += 1
        else:
            refined_chapters.append((current_title, current_lines))
            i += 1            
    return refined_chapters
def verify_and_report_final(output_dir, chapters_with_notes):
    if not os.path.exists(output_dir): return
    files = [f for f in os.listdir(output_dir) if f.endswith(".txt")]            
    def get_sort_key(filename):
        match_chapter = re.search(r'(?:Chương|Chapter|第|Hồi)\s*(\d+)', filename, re.IGNORECASE)
        if match_chapter:
            return int(match_chapter.group(1))
        nums = re.findall(r'\d+', filename)
        return int(nums[0]) if nums else 0            
    files.sort(key=get_sort_key)
    safe_notes = {sanitize_filename(name) for name in chapters_with_notes}
    print(f"\n{'STT':<5} {'DUNG LƯỢNG':<12} {'[TG]':<6} {'TÊN FILE'}")
    print("-" * 80)    
    for idx, f in enumerate(files):
        size = os.path.getsize(os.path.join(output_dir, f))
        file_name_no_ext = os.path.splitext(f)[0]
        has_note = "[v]" if file_name_no_ext in safe_notes else ""
        print(f"{idx+1:<5} {size:<12} {has_note:<6} {f}")
def create_epub_file(output_path, book_title, chapters, author="Unknown", cover_path=None):
    """Tạo file EPUB từ danh sách chương mà không cần thư viện ngoài"""
    print(f"📚 Đang đóng gói EPUB: {output_path} ...")    
    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr("mimetype", "application/epub+zip", zipfile.ZIP_STORED)           
            container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
            z.writestr("META-INF/container.xml", container_xml)            
            manifest_items = []
            spine_refs = []
            nav_points = []            
            css_content = '''body { font-family: "Times New Roman", serif; line-height: 1.5; margin: 5%; }
h2 { text-align: center; color: #333; page-break-after: avoid; }
p { text-indent: 2em; margin-bottom: 0.5em; text-align: justify; }
.cover { text-align: center; height: 100%; }
.cover img { max-width: 100%; max-height: 100%; }'''
            z.writestr("OEBPS/style.css", css_content)
            manifest_items.append('<item id="style" href="style.css" media-type="text/css"/>')
            cover_meta = ""
            if cover_path and os.path.exists(cover_path):
                ext = os.path.splitext(cover_path)[1].lower().replace('.', '')
                media_type = "image/jpeg" if ext in ['jpg', 'jpeg'] else "image/png"
                z.write(cover_path, f"OEBPS/cover.{ext}")
                manifest_items.append(f'<item id="cover-image" href="cover.{ext}" media-type="{media_type}"/>')
                cover_meta = '<meta name="cover" content="cover-image"/>'
                cover_html = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Cover</title><link href="style.css" rel="stylesheet" type="text/css"/></head>
<body><div class="cover"><img src="cover.{ext}" alt="Cover"/></div></body></html>'''
                z.writestr("OEBPS/cover.html", cover_html)
                manifest_items.append('<item id="cover-page" href="cover.html" media-type="application/xhtml+xml"/>')
                spine_refs.append('<itemref idref="cover-page"/>')
            for idx, (title, lines) in enumerate(chapters):
                file_name = f"chapter_{idx+1}.html"
                html_body = []
                html_body.append(f'<h2>{html.escape(title)}</h2>')
                for line in lines:
                    if not line.strip(): continue
                    clean_line = line.strip().lstrip("　 \t")
                    html_body.append(f'<p>{html.escape(clean_line)}</p>')                
                html_content = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>{html.escape(title)}</title><link href="style.css" rel="stylesheet" type="text/css"/></head>
<body>
{"".join(html_body)}
</body></html>'''                
                z.writestr(f"OEBPS/{file_name}", html_content)               
                item_id = f"chap{idx+1}"
                manifest_items.append(f'<item id="{item_id}" href="{file_name}" media-type="application/xhtml+xml"/>')
                spine_refs.append(f'<itemref idref="{item_id}"/>')
                nav_points.append(f'<navPoint id="nav{idx+1}" playOrder="{idx+1}"><navLabel><text>{html.escape(title)}</text></navLabel><content src="{file_name}"/></navPoint>')            
            opf_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookID" version="2.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <dc:title>{html.escape(book_title)}</dc:title>
        <dc:creator>{author}</dc:creator>
        <dc:language>vi</dc:language>
        <dc:identifier id="BookID" opf:scheme="UUID">{uuid.uuid4()}</dc:identifier>
        {cover_meta}
    </metadata>
    <manifest>
        <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
        {"".join(manifest_items)}
    </manifest>
    <spine toc="ncx">
        {"".join(spine_refs)}
    </spine>
</package>'''
            z.writestr("OEBPS/content.opf", opf_content)
            ncx_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta name="dtb:uid" content="{uuid.uuid4()}"/>
        <meta name="dtb:depth" content="1"/>
        <meta name="dtb:totalPageCount" content="0"/>
        <meta name="dtb:maxPageNumber" content="0"/>
    </head>
    <docTitle><text>{book_title}</text></docTitle>
    <navMap>
        {"".join(nav_points)}
    </navMap>
</ncx>'''
            z.writestr("OEBPS/toc.ncx", ncx_content)            
        print("✅ Đã tạo EPUB thành công!")
    except Exception as e:
        print(f"❌ Lỗi khi tạo EPUB: {e}")
        log_error(book_title, f"Lỗi tạo EPUB: {e}")
def split_and_format_v6_reindex(input_file, start_chapter_num=1, signature_text="", 
                                output_mode="split", is_silent=False, indent_str="\u3000\u3000", keep_original_numbering=False):
    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_dir = ""    
    replacements = load_replacements()    
    garbage_patterns = load_garbage_patterns() 
    if output_mode == "split":
        output_dir = os.path.join(os.path.dirname(input_file), f"{base_name}_Split")
        if not os.path.exists(output_dir): os.makedirs(output_dir)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
    lines = []    
    file_size = os.path.getsize(input_file)
    limit = 10 * 1024 * 1024    
    encodings = ['utf-8-sig', 'utf-16', 'gb18030', 'utf-8']    
    for enc in encodings:
        try:
            if file_size < limit:
                if not is_silent: print(f"📖 Đang nạp dữ liệu và xử lý thay thế từ điển...", end='', flush=True)
                with open(input_file, 'r', encoding=enc) as f:
                    full_text = f.read()
                    full_text = clean_common_entities(full_text)
                    full_text = apply_replacements(full_text, replacements)
                    lines = full_text.splitlines()
                if not is_silent: print(" Hoàn tất!", flush=True)
            else:
                if not is_silent: print(f"File lớn ({file_size/1024/1024:.1f}MB), dùng chế độ đọc từng dòng để tiết kiệm RAM...")
                with open(input_file, 'r', encoding=enc) as f:
                    for line in f:
                        l = clean_common_entities(line)
                        l = apply_replacements(l, replacements)
                        lines.append(l.rstrip('\n'))
            if lines: break
        except: continue                                   
    if not lines: 
        print(f"❌ Không đọc được file: {input_file}")
        log_error(base_name, "Không đọc được file hoặc file trống.")
        return        
    re_eq_sep = re.compile(r'^\s*={10,}\s*$')
    re_dash_long = re.compile(r'^\s*-{40,}\s*$')    
    re_note_for_equals_mode = re.compile(r'^\s*(-{20,})\s*$')
    re_note_for_dash_mode = re.compile(r'^\s*([_*]{5,}|[—–─]{7,})\s*$')
    re_note_default = re.compile(r'^\s*([_*]{5,}|-{6,39}|[—–─]{7,})\s*$')
    note_keywords = ["作者有话说", "发表于", "小剧场", "求月票", "求收藏", "PS:", "ps:"]
    re_susuinian_strict = re.compile(r'^(\[.*?\]|（.*?）)?碎碎念[:：]\s*$')                                                 
    eq_count = sum(1 for l in lines if re_eq_sep.match(l))
    dash_long_count = sum(1 for l in lines if re_dash_long.match(l))    
    if eq_count > dash_long_count and eq_count > 2:
        mode = "PRIORITY_EQUALS"
    elif dash_long_count >= eq_count and dash_long_count > 2:
        mode = "PRIORITY_DASH_LONG"
    else:
        mode = "FALLBACK_KEYWORDS"           
    if not is_silent: print(f"[{base_name}] Thống kê: [=]: {eq_count} | [-]: {dash_long_count} -> MODE: {mode}")    
    chapters = []
    raw_titles_for_check = []
    current_title = "Phần mở đầu"
    current_lines = []
    temp_idx = start_chapter_num 
    i = 0
    total_lines = len(lines)
    decision_history = []     
    while i < total_lines:
        line = lines[i].strip()
        raw_line = lines[i]
        is_new_chapter = False
        raw_title = ""
        jump_to = i                
        found_sep = False
        if re_eq_sep.match(raw_line): found_sep = True
        elif mode == "PRIORITY_EQUALS" and re_eq_sep.match(line): found_sep = True
        elif mode == "PRIORITY_DASH_LONG" and re_dash_long.match(line): found_sep = True
        if found_sep:
            check_directions = ["DOWN", "UP"] if mode == "PRIORITY_DASH_LONG" else ["UP", "DOWN"]            
            for direction in check_directions:
                if is_new_chapter: break
                if direction == "UP":
                    k = i - 1
                    while k >= 0 and not lines[k].strip():
                        k -= 1
                    if k >= 0:
                        prev_line = lines[k].strip()
                        if len(prev_line) < 150:
                            if current_lines and current_lines[-1].strip() == prev_line:
                                raw_title = current_lines.pop()
                                is_new_chapter = True
                                jump_to = i                 
                elif direction == "DOWN":
                    next_idx = i + 1
                    while next_idx < total_lines and not lines[next_idx].strip(): next_idx += 1
                    if next_idx < total_lines:
                        raw_title = lines[next_idx].strip()
                        if len(raw_title) > 80:
                            is_new_chapter = False
                        else:
                            is_new_chapter = True
                            jump_to = next_idx
                    else:
                        break
        if not is_new_chapter:
            re_explicit = re.compile(r'^\s*(番外|第\s*[0-9一二三四五六七八九十百千万]+\s*[章卷]|Quyển\s*[0-9一二三四五六七八九十百千万\d]+|Chương\s*\d+|Chapter\s*\d+|Hồi\s*\d+|^\d+[.,、\s]+|^\d+$)', re.IGNORECASE)            
            is_digit_dot_title = re.match(r'^\d+[\.,]{2,}', line) 
            if (re_explicit.match(line) or is_digit_dot_title) and len(line) < 150:
                next_is_sep = False                
                k = i + 1
                while k < total_lines and not lines[k].strip():
                    k += 1               
                if k < total_lines:
                    l_next = lines[k].strip()
                    if mode == "PRIORITY_EQUALS" and re_eq_sep.match(l_next): 
                        next_is_sep = True
                    elif mode == "PRIORITY_DASH_LONG" and re_dash_long.match(l_next): 
                        next_is_sep = True                
                if next_is_sep:
                    is_new_chapter = True
                    raw_title = line
                    jump_to = k 
                else:
                    is_digit_start = re.match(r'^\d+', line)
                    should_ask = (mode in ["PRIORITY_EQUALS", "PRIORITY_DASH_LONG"]) or (is_digit_start and not is_digit_dot_title)                    
                    if is_digit_dot_title: should_ask = False
                    if should_ask:
                        if is_silent:
                            if is_digit_start and re.search(r'^\d+[、\.,]\s*\d+[、\.,]', line):
                                 is_new_chapter = False
                            elif is_digit_start and len(line) < 4: 
                                 is_new_chapter = False
                            else:
                                 is_new_chapter = True
                                 raw_title = line
                                 jump_to = i
                        else:
                            snapshot = (i, list(chapters), current_title, list(current_lines), temp_idx, list(raw_titles_for_check))
                            do_rollback = False
                            while True:
                                reason = "SỐ ĐẦU DÒNG (Dễ nhầm liệt kê)" if is_digit_start else f"MODE {mode}"
                                print(f"\n{'?'*10} PHÁT HIỆN NGHI VẤN [{reason}] {'?'*10}")
                                print(f"📌 Dòng: {line}")
                                print("👉 Lựa chọn:")
                                print("   [1] TÁCH CHƯƠNG (Đây là tiêu đề)")
                                print("   [2] BỎ QUA (Đây là nội dung/đếm ngược/liệt kê)")
                                print("   [b] QUAY LẠI (Undo quyết định trước đó)")
                                choice = input("   Nhập (Enter=2, b=Back): ").strip()                               
                                if choice.lower() == 'b':
                                    if not decision_history:
                                        print("⚠️ Không thể quay lại xa hơn!")
                                        continue
                                    else:
                                        (i, chapters, current_title, current_lines, temp_idx, raw_titles_for_check) = decision_history.pop()
                                        do_rollback = True
                                        print("⏪ Đã quay lại điểm quyết định trước đó!")
                                        break
                                if choice == '1':
                                    is_new_chapter = True
                                    raw_title = line
                                    jump_to = i
                                    decision_history.append(snapshot)
                                    break
                                elif choice == '2' or choice == '':
                                    is_new_chapter = False
                                    decision_history.append(snapshot)
                                    break                        
                            if do_rollback:
                                continue
                    else:
                        is_new_chapter = True
                        raw_title = line
                        jump_to = i                       
        if is_new_chapter:
            if len(raw_title) > 30:
                if is_silent:
                    if len(raw_title) < 100:
                        i = jump_to
                    else:
                        is_new_chapter = False
                else:
                    snapshot = (i, list(chapters), current_title, list(current_lines), temp_idx, list(raw_titles_for_check))
                    do_rollback = False                    
                    while True:
                        print(f"\n{'!'*10} CẢNH BÁO TIÊU ĐỀ DÀI ({len(raw_title)} ký tự) {'!'*10}")
                        print(f"🔎 Nội dung: {raw_title}")
                        print("👉 Lựa chọn:")
                        print("   [1] CHẤP NHẬN tách chương (Đây là tiêu đề)")
                        print("   [2] BỎ QUA và gộp (Đây là nội dung văn bản)")
                        print("   [b] QUAY LẠI (Undo quyết định trước đó)")
                        choice = input("   Nhập (Enter=1, b=Back): ").strip()                        
                        if choice.lower() == 'b':
                            if not decision_history:
                                print("⚠️ Không thể quay lại xa hơn!")
                                continue
                            else:
                                (i, chapters, current_title, current_lines, temp_idx, raw_titles_for_check) = decision_history.pop()
                                do_rollback = True
                                print("⏪ Đã quay lại điểm quyết định trước đó!")
                                break
                        if choice == '2':
                            is_new_chapter = False
                            decision_history.append(snapshot)
                            break
                        else:
                            i = jump_to
                            decision_history.append(snapshot)
                            break                            
                    if do_rollback:
                        continue
            else:
                i = jump_to                        
        if is_new_chapter:
            raw_titles_for_check.append(raw_title)
            potential_clean_title = clean_chapter_title(raw_title, temp_idx)            
            if current_lines: 
                chapters.append((current_title, current_lines))            
            current_title = potential_clean_title            
            current_lines = [raw_title]            
            temp_idx += 1
        else:
            if line:
                cleaned = clean_garbage_text(line, garbage_patterns)
                cleaned = normalize_punctuation(cleaned)
                current_lines.append(cleaned)
        i += 1           
    if current_lines: chapters.append((current_title, current_lines))   
    if not is_silent: check_sequence_gaps(raw_titles_for_check)
    chapters = interactive_check_chapters(chapters, is_silent)                    
    final_processed_chapters = []
    current_idx = start_chapter_num    
    total_chars = 0
    chapters_with_notes = []           
    for idx, (raw_name, content) in enumerate(chapters):
        if not content: continue                      
        while len(content) > 1:
            last_line = content[-1].strip()
            if re_note_default.match(last_line) or re_note_for_equals_mode.match(last_line) or re_note_for_dash_mode.match(last_line) or not last_line:
                content.pop()
            else:
                break               
        new_content = [content[0]]
        body_lines = content[1:]
        split_point = -1
        last_sep_pos = -1 
        note_found_in_this_chapter = False                                              
        search_range = range(len(body_lines)-1, max(-1, len(body_lines)-20), -1)                
        for j in search_range:
            l = body_lines[j].strip()
            if not l: continue                    
            is_kw_normal = any(l.startswith(kw) for kw in note_keywords)
            is_kw_strict = bool(re_susuinian_strict.match(l)) and len(l) <= 10            
            is_kw = is_kw_normal or is_kw_strict                        
            if mode == "PRIORITY_DASH_LONG":
                is_sep = False
            else:
                is_sep = (re_note_for_equals_mode.match(l) or 
                          re_note_for_dash_mode.match(l) or 
                          re_note_default.match(l))
                if is_sep and len(l) > 25: is_sep = False                                  
            if is_kw:
                split_point = j
                note_found_in_this_chapter = True
                break
            elif is_sep and split_point == -1:
                has_content_below = any(body_lines[k].strip() for k in range(j + 1, len(body_lines)))
                if has_content_below:
                    last_sep_pos = j
                    note_found_in_this_chapter = True                
        if split_point == -1:
            split_point = last_sep_pos                    
        for k, line in enumerate(body_lines):
            l_strip = line.strip()
            if not l_strip: continue                        
            if k == split_point:
                new_content.append(f"\n{indent_str}【作者有话说】")
                is_pure_sep = (re_note_for_equals_mode.match(l_strip) or re_note_for_dash_mode.match(l_strip) or re_note_default.match(l_strip))
                if not is_pure_sep:
                    clean_l = re.sub(r'^(作者有话说|发表于|小剧场|求月票|求收藏|PS:|ps:|.*碎碎念[:：])', '', l_strip).strip("：: -=")
                    if clean_l: new_content.append(f"{indent_str}" + clean_l)
            else:
                new_content.append(f"{indent_str}" + l_strip)        
        raw_name = raw_name.strip()
        prefix_pattern = r'^(第\s*[0-9一二三四五六七八九十百千万\s]+\s*[章回卷]|Quyển\s*[0-9一二三四五六七八九十百千万\d]+|Chương\s*\d+|Chapter\s*\d+|Hồi\s*\d+|分卷阅读\s*\d*|\d+[\s\.\-、]+)'
        if idx == 0 and any(k in raw_name.lower() for k in ["mở đầu", "văn án"]):
            new_title_str = raw_name
        else:
            original_title_line = content[0].strip()           
            clean_text = re.sub(prefix_pattern, '', original_title_line, flags=re.IGNORECASE).strip()
            clean_text = re.sub(prefix_pattern, '', clean_text, flags=re.IGNORECASE).strip()
            clean_text = clean_text.strip(" -=—–─_*　：:,，.、")            
            is_fanwai = False
            if "番外" in original_title_line or "fanwai" in original_title_line.lower():
                is_fanwai = True
                if "番外" not in clean_text:
                    clean_text = "番外 " + clean_text
            if keep_original_numbering:
                real_num = -1                
                match_arab = re.search(r'(?:第|Chương|Chapter|Chap|Hồi|Part|Vol|Quyển)?\s*([0-9]+)\s*[.:\-章回卷\s]', original_title_line, re.IGNORECASE)
                if match_arab:
                    real_num = int(match_arab.group(1))
                elif not match_arab:
                    match_cn = re.search(r'第\s*([零一二三四五六七八九十百千万]+)\s*[章回卷]', original_title_line)
                    if match_cn:
                        real_num = cn_to_int(match_cn.group(1))
                if real_num > 0:
                    if is_fanwai and real_num < current_idx:
                        pass 
                    else:
                        current_idx = real_num           
            new_title_str = f"第{current_idx}章 {clean_text}"            
            current_idx += 1                                                                         
        if note_found_in_this_chapter:
            chapters_with_notes.append(new_title_str)                                                                          
        total_chars += len("".join(map(str, new_content[1:])).strip())
        new_content[0] = new_title_str       
        if signature_text: new_content.append("\n" + signature_text)        
        final_processed_chapters.append((new_title_str, new_content))   
    if not is_silent: print(f"\n⚡ Đang xuất file dưới dạng: {output_mode.upper()}...")   
    if output_mode == "split":
        count = 0
        for title, content in final_processed_chapters:
            safe_name = sanitize_filename(title)            
            try:
                with open(os.path.join(output_dir, f"{safe_name}.txt"), 'w', encoding='utf-8-sig') as f:
                    f.write('\n'.join(map(str, content)))
                count += 1
            except Exception as e:
                log_error(base_name, f"Lỗi ghi chương {title}: {e}")
        if not is_silent:
            print(f"\n" + " TỔNG KẾT DỮ LIỆU ".center(60, "="))
            print(f"📊 Tổng số chương: {count}")
            print(f"📝 Tổng ký tự nội dung: {total_chars:,}")
            print(f"📂 Thư mục: {output_dir}")
            print(f"💡 Chú thích: [v] = Chương có lời tác giả")
            verify_and_report_final(output_dir, chapters_with_notes)            
    elif output_mode == "merge":
        out_file = os.path.join(os.path.dirname(input_file), f"{base_name}_cleaned.txt")
        try:
            with open(out_file, 'w', encoding='utf-8-sig') as f:
                f.write('\n\n'.join(['\n'.join(map(str, c)) for t, c in final_processed_chapters]))
            print(f"✅ Đã gộp file: {out_file}")
        except Exception as e:
            log_error(base_name, f"Lỗi ghi file merge: {e}") 
    elif output_mode == "epub":
        out_file = os.path.join(os.path.dirname(input_file), f"{base_name}.epub")
        epub_chapters = []
        for t, c in final_processed_chapters:
            epub_chapters.append((t, c[1:]))
        cover_path = None
        input_dir = os.path.dirname(input_file)
        possible_names = ["cover.jpg", "cover.png", f"{base_name}.jpg", f"{base_name}.png"]
        for p in possible_names:
            full_p = os.path.join(input_dir, p)
            if os.path.exists(full_p):
                cover_path = full_p
                print(f"🖼️ Phát hiện ảnh bìa: {p}")
                break       
        create_epub_file(out_file, base_name, epub_chapters, cover_path=cover_path)
if __name__ == "__main__":
    check_for_updates()
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILE = os.path.join(BASE_DIR, "signature_config.txt")    
    if not os.path.exists(REPLACEMENT_CONFIG_FILE):
        with open(REPLACEMENT_CONFIG_FILE, 'w', encoding='utf-8-sig') as f:
            f.write("vietnam=Việt Nam\nkhựa=Trung Quốc\n")
    if not os.path.exists(GARBAGE_CONFIG_FILE):
        with open(GARBAGE_CONFIG_FILE, 'w', encoding='utf-8-sig') as f:
             f.write("https://.*\nwww\\..*\n")
    def load_signature():
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as f:
                    return f.read().strip()
            except: return ""
        return ""    
    def save_signature(text):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8-sig') as f:
                f.write(text)
            return True
        except Exception as e:
            print(f"⚠️ Lỗi không thể lưu file ghi nhớ: {e}")
            return False                
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        print(" TOOL CLEAN RAW ".center(70, "="))
        print("💡 Hỗ trợ: Kéo thả 1 File .txt HOẶC 1 Thư mục (Batch Mode)")        
        try:
            path_input = input("👉 Đường dẫn: ").strip('"').strip("'").strip()
            if path_input.lower() in ['q', 'exit']: break                                                                    
            target_files = []
            if os.path.isfile(path_input):
                target_files.append(path_input)
            elif os.path.isdir(path_input):
                print(f"📂 Đã phát hiện thư mục. Đang quét file .txt...")
                for root, dirs, files in os.walk(path_input):
                    for file in files:
                        if file.lower().endswith(".txt") and "_Split" not in root:
                            target_files.append(os.path.join(root, file))
                print(f"📊 Tìm thấy {len(target_files)} file .txt")
            else:
                print("❌ Đường dẫn không tồn tại.")
                input("Nhấn Enter để quay lại...")
                continue                
            if not target_files:
                input("❌ Không có file nào để xử lý. Enter...")
                continue
            output_mode = "split"
            is_silent = False
            indent_str = "\u3000\u3000"
            keep_original = False
            start_num = 1
            sig = ""
            step = 1
            cancel_process = False            
            while step <= 6:
                os.system('cls' if os.name == 'nt' else 'clear')
                print(f"📂 Đang thiết lập cho: {os.path.basename(path_input)}")
                print(f"ℹ️  Tìm thấy: {len(target_files)} files")
                print("(💡 Mẹo: Nhập 'b' và Enter để quay lại bước trước)\n")
                if step == 1:
                    print("⚙️ [1/6] CẤU HÌNH ĐỊNH DẠNG:")
                    print("1. Xuất ra Folder từng chương (Split)")
                    print("2. Xuất ra 1 File gộp (Merge Txt)")
                    print("3. Xuất ra Ebook (EPUB)")
                    out_choice = input("👉 Chọn định dạng (Enter=1): ").strip()
                    if out_choice.lower() == 'b': 
                        cancel_process = True
                        break                    
                    output_mode = "split"
                    if out_choice == '2': output_mode = "merge"
                    elif out_choice == '3': output_mode = "epub"
                    step += 1
                elif step == 2:
                    print(f"🤖 [2/6] CHẾ ĐỘ TỰ ĐỘNG (SILENT MODE)?")
                    print("   [y] Có (Tự sửa lỗi, không hỏi, thích hợp treo máy)")
                    print("   [n] Không (Dừng lại hỏi khi gặp lỗi - An toàn hơn)")
                    silent_input = input("👉 Chọn (y/n, Enter=n): ").lower().strip()
                    if silent_input == 'b':
                        step = 1
                        continue
                    is_silent = (silent_input == 'y')
                    step += 1
                elif step == 3:
                    print("\n📝 [3/6] KIỂU THỤT ĐẦU DÒNG:")
                    print("   [1] Chuẩn Trung (2 ký tự 　　)")
                    print("   [2] Chuẩn Việt (1 Tab)")
                    print("   [3] 4 Dấu cách") 
                    indent_choice = input("👉 Chọn (Enter=1): ").strip()
                    if indent_choice.lower() == 'b':
                        step = 2
                        continue
                    indent_str = "\u3000\u3000"
                    if indent_choice == '2': indent_str = "\t"
                    elif indent_choice == '3': indent_str = "    "
                    step += 1
                elif step == 4:
                    print("\n🔢 [4/6] CHẾ ĐỘ ĐÁNH SỐ CHƯƠNG:")
                    print("   [1] Tự động đánh lại (1, 2, 3...) - Nên dùng nếu file đầy đủ toàn bộ từ 1 đến hết")
                    print("   [2] Giữ nguyên số của tác giả (Theo file gốc) - Nên dùng nếu file là các chương không bắt đầu từ 1")
                    num_mode_choice = input("👉 Chọn (Enter=1): ").strip()
                    if num_mode_choice.lower() == 'b':
                        step = 3
                        continue
                    keep_original = (num_mode_choice == '2')
                    step += 1
                elif step == 5:
                    if len(target_files) > 1 or keep_original:
                        step += 1
                        continue                        
                    print("\n🔢 [5/6] THIẾT LẬP SỐ CHƯƠNG:")
                    s_num = input("👉 Số chương bắt đầu (Enter=1): ").strip()
                    if s_num.lower() == 'b':
                        step = 4
                        continue
                    start_num = int(s_num) if s_num.isdigit() else 1
                    step += 1
                elif step == 6:
                    print("\n✍️ [6/6] CHỮ KÝ CUỐI CHƯƠNG:")
                    saved_sig = load_signature()
                    sig = ""
                    if saved_sig:
                        print(f"⭐ Chữ ký đang nhớ: {saved_sig}")
                        sig_input = input("👉 Enter dùng lại, nhập mới để đổi, 'x' xóa: ").strip()
                        if sig_input.lower() == 'b':
                            if len(target_files) > 1 or keep_original:
                                step = 4
                            else:
                                step = 5
                            continue                        
                        if sig_input == "": sig = saved_sig
                        elif sig_input.lower() == 'x': 
                            save_signature("")
                            print("✅ Đã xóa chữ ký.")
                        else: 
                            sig = sig_input
                            save_signature(sig)
                    else:
                        sig_input = input("👉 Nhập chữ ký (Enter bỏ qua): ").strip()
                        if sig_input.lower() == 'b':
                            if len(target_files) > 1 or keep_original:
                                step = 4
                            else:
                                step = 5
                            continue
                        if sig_input:
                            sig = sig_input
                            save_signature(sig)
                    step += 1            
            if cancel_process:
                continue
            print(f"\n🚀 BẮT ĐẦU XỬ LÝ {len(target_files)} FILE...\n")
            if is_silent and len(target_files) > 1:
                print(f"⚡ Đang chạy chế độ ĐA LUỒNG (Max 4 tiến trình)...")
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                    futures = []
                    for fpath in target_files:
                        futures.append(executor.submit(
                            split_and_format_v6_reindex,
                            input_file=fpath,
                            start_chapter_num=start_num,
                            signature_text=sig,
                            output_mode=output_mode,
                            is_silent=True,
                            indent_str=indent_str,
                            keep_original_numbering=keep_original
                        ))
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            future.result()
                        except Exception as e:
                            print(f"❌ Có lỗi trong thread: {e}")
            else:
                for idx, fpath in enumerate(target_files):
                    print(f"⏳ [{idx+1}/{len(target_files)}] Processing: {os.path.basename(fpath)}...")
                    try:
                        split_and_format_v6_reindex(
                            input_file=fpath,
                            start_chapter_num=start_num,
                            signature_text=sig,
                            output_mode=output_mode,
                            is_silent=is_silent,
                            indent_str=indent_str,
                            keep_original_numbering=keep_original
                        ) 
                    except Exception as e:
                        print(f"❌ Lỗi file {fpath}: {e}")
                        log_error(os.path.basename(fpath), f"Critical Error: {e}")
                        traceback.print_exc()            
            print("\n✅ HOÀN TẤT TẤT CẢ TÁC VỤ.")            
        except Exception as e: 
            print(f"❌ Lỗi Critical: {e}")
            log_error("SYSTEM", f"Critical System Error: {e}")
            traceback.print_exc()
            input("\nNhấn Enter để tiếp tục...")                      
        if input("\nTiếp tục xử lý đợt khác? (y/n): ").lower() == 'n': break

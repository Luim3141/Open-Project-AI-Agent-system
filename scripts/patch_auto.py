path = 'openproject/ai/gateway/engineering_auto.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

target = "    return {'scheduled': False, 'reason': reason, 'mode': 'OFF'}"
replacement = "    explanation = 'Toàn bộ 5/5 Backlog units hiện tại đã hoàn tất giao hàng. Chế độ AUTO tự động tắt an toàn để bảo vệ hệ thống.' if all_delivered else 'Không có unit nào đủ điều kiện kích hoạt tự động.'\n    return {'scheduled': False, 'reason': reason, 'mode': 'OFF', 'explanation': explanation}"

assert target in text, "target not found in engineering_auto.py"
text = text.replace(target, replacement, 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated engineering_auto.py successfully")

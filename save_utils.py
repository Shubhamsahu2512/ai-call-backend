# save_utils.py
from openpyxl import Workbook

def append_conversation_and_save_excel(conversation, filename="call_log.xlsx"):
    wb = Workbook()
    ws = wb.active 
    ws.append(["Speaker", "Text"])
    for speaker, text in conversation:
        ws.append([speaker, text]) 
        wb.save(filename)
    return filename
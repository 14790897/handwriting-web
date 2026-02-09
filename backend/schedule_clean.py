import schedule
import time
import shutil
import os
import threading

def clear_temp_dir():
    temp_dir = './temp'
    if os.path.exists(temp_dir):
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')

# 安排清理任务每天零点执行
schedule.every().day.at("00:00").do(clear_temp_dir)

def run_schedule():
    schedule.every().day.at("00:00").do(clear_temp_dir)
    while True:
        schedule.run_pending()
        time.sleep(1000)
        
def start_schedule_thread():
    # 创建一个新的线程来运行清理任务的计划
    schedule_thread = threading.Thread(target=run_schedule)
    # 设置为守护线程，这样当主线程退出时，它也会退出
    schedule_thread.daemon = True
    # 启动线程
    schedule_thread.start()

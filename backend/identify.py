import cv2
import numpy as np
from sklearn.cluster import DBSCAN

def get_avg_distance(distances):
    # 将列表转化为 N x 1 的矩阵，因为DBSCAN需要这种格式的输入
    distances_np = np.array(distances).reshape(-1, 1)

    # 使用DBSCAN算法
    clustering = DBSCAN(eps=3, min_samples=2).fit(distances_np)

    # 找出最常见的标签（除了-1，-1代表噪声）
    labels, counts = np.unique(clustering.labels_, return_counts=True)
    most_common_label = labels[np.argmax(counts[labels != -1])]

    # 选择最常见的聚类中的间距，并计算这些间距的平均值
    selected_distances = distances_np[clustering.labels_ == most_common_label]
    avg_distance = np.mean(selected_distances)
    return avg_distance

def identify_distance(filename):
    # 读取图像
    image = cv2.imread(filename)

    # 转化为灰度图像
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 二值化
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)

    # 使用形态学操作来连接线条的两侧
    kernel = np.ones((5,5),np.uint8)
    dilated = cv2.dilate(binary, kernel, iterations = 1)
    eroded = cv2.erode(dilated, kernel, iterations = 1)
    
    # 边缘检测
    edges = cv2.Canny(eroded, 50, 150, apertureSize=3)

    # 直线检测
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)

    lines = sorted(lines, key=lambda x: x[0][1])

    # 选择线，计算旋转角度并存储
    angles = []
    for line in lines:
        for x1, y1, x2, y2 in line:
            print('x1:', x1, 'y1:', y1, 'x2:', x2, 'y2:', y2)
            angle = np.arctan2(y2 - y1, x2 - x1) * 180. / np.pi
            angles.append(angle)

    # 计算平均角度
    avg_angle = np.mean(angles)

    # 得到旋转矩阵
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, avg_angle, 1.0)

    # 执行旋转
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, 
                            borderMode=cv2.BORDER_REPLICATE)

    # cv2.imshow('Rotated', rotated)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # 转换为灰度图像
    gray_rotated = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY)

    # 二值化
    _, binary_rotated = cv2.threshold(gray_rotated, 150, 255, cv2.THRESH_BINARY_INV)

    # 边缘检测
    edges_rotated = cv2.Canny(binary_rotated, 50, 150, apertureSize=3)

    # 直线检测
    lines_rotated = cv2.HoughLinesP(edges_rotated, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)

    # 对直线的y坐标进行排序
    lines_rotated = sorted(lines_rotated, key=lambda x: x[0][1])


    # 初始化空列表来存储每行的空白长度
    l_whitespaces = []
    r_whitespaces = []

    for line in lines_rotated:
        for x1, y1, x2, y2 in line:
            # 提取每行像素
            row = binary_rotated[y1]
            # 找到左边第一个非空白像素
            left = np.where(row == 255)[0][0] if np.where(row == 255)[0].size != 0 else 0
            # 找到右边第一个非空白像素
            right = np.where(row == 255)[0][-1] if np.where(row == 255)[0].size != 0 else len(row)
            # 计算空白长度
            whitespace_left = x1 - left
            whitespace_right = right - x2
            l_whitespaces.append(whitespace_left)
            r_whitespaces.append(whitespace_right)
            # print('左空白：', whitespace_left,'右空白：',whitespace_right)

    avg_l_whitespace = get_avg_distance(l_whitespaces)
    avg_r_whitespace = get_avg_distance(r_whitespaces)

    distances = []

    for i in range(1, len(lines_rotated)):
        distance=lines_rotated[i][0][1] - lines_rotated[i-1][0][1]
        if distance > 5:
            distances.append(distance)
            # print('行间距：', distance)
            
    avg_distance = get_avg_distance(distances)
    print('左边平均空白长度：', avg_l_whitespace)
    print('右边平均空白长度：', avg_r_whitespace)
    print('平均行间距：', avg_distance)
    
    return avg_l_whitespace, avg_r_whitespace, avg_distance

if __name__ == '__main__':
    identify_distance('notebook.jpg')
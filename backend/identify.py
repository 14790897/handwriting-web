import cv2
import numpy as np
from sklearn.cluster import DBSCAN

#有bug时，别忘了打断点 7.6
def get_avg_distance(distances):
    # 将列表转化为 N x 1 的矩阵，因为DBSCAN需要这种格式的输入
    distances_np = np.array(distances).reshape(-1, 1)

    # 使用DBSCAN算法
    clustering = DBSCAN(eps=5, min_samples=3).fit(distances_np)

    # 找出最常见的标签（除了-1，-1代表噪声）
    labels, counts = np.unique(clustering.labels_, return_counts=True)
    # print('clustering.labels_:', clustering.labels_)
    # print('labels:', labels)
    # print('counts:', counts)
    counts[labels == -1] = 0
    most_common_label = labels[np.argmax(counts)]
    #下面这句代码存在问题，false时会把这个数据删除，而没有进行占位 7.6
    # most_common_label = labels[np.argmax(counts[labels != -1])]
    # print(counts[labels != -1])
    # print('most_common_label:', most_common_label)
    # 选择最常见的聚类中的间距，并计算这些间距的平均值
    selected_distances = distances_np[clustering.labels_ == most_common_label]
    # print('selected_distances:', selected_distances)
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
            # 找到左边第一个非空白像素，第一个零是为了去掉外面的元组
            left = np.where(row == 255)[0][0] if np.where(row == 255)[0].size != 0 else 0
            # 找到右边第一个非空白像素
            right = np.where(row == 255)[0][-1] if np.where(row == 255)[0].size != 0 else len(row)
            # 计算空白长度
            if x1 != 0 and x2 != len(row):
                whitespace_left = x1 #x1 - left
                whitespace_right = len(row) - x2 #right - x2
                l_whitespaces.append(whitespace_left)
                r_whitespaces.append(whitespace_right)
            # print('左空白：', whitespace_left,'右空白：',whitespace_right)

    avg_l_whitespace = get_avg_distance(l_whitespaces)
    avg_r_whitespace = get_avg_distance(r_whitespaces)
    
    # 初始化空列表来存储每列的空白长度
    t_whitespaces = []
    b_whitespaces = []

    # 转置图像，使得列变成行
    binary_rotated_T = binary_rotated.T

    for column in binary_rotated_T:
        # 找到上方第一个非空白像素
        top = np.where(column == 255)[0][0] if np.where(column == 255)[0].size != 0 else 0
        # 找到下方第一个非空白像素
        bottom = np.where(column == 255)[0][-1] if np.where(column == 255)[0].size != 0 else len(column)
        # 计算空白长度
        if top != 0 and bottom != len(column):
            whitespace_top = top
            whitespace_bottom = len(column) - bottom
            t_whitespaces.append(whitespace_top)
            b_whitespaces.append(whitespace_bottom)

    print('上边空白长度：', t_whitespaces)
    avg_t_whitespace = get_avg_distance(t_whitespaces)
    avg_b_whitespace = get_avg_distance(b_whitespaces)

    # 输出空白长度
    print('上边空白长度：', avg_t_whitespace)
    print('下边空白长度：', avg_b_whitespace)


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
    
    return avg_l_whitespace, avg_r_whitespace, avg_t_whitespace, avg_b_whitespace, avg_distance

if __name__ == '__main__':
    identify_distance('notebook.jpg')
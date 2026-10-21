import cv2
import numpy as np
from sklearn.cluster import DBSCAN


class ImageIdentificationError(Exception):
    """这张图识别不出页边距：要么读不出图片，要么整页找不到可用横线。

    调用方（/api/imagefileprocess）应当把它转成给用户看的提示、让用户手动填写，
    而不是当成 500；更不能用全 0 之类的占位值去覆盖用户已经填好的参数。
    """


#有bug时，别忘了打断点 7.6
def get_avg_distance(distances):
    # 空输入直接退化为 0：整页找不到直线（纯白图）时下游不该崩，
    # 否则 DBSCAN 拿到空簇、np.argmax 会对空数组抛 ValueError
    if len(distances) == 0:
        return 0

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

    # 扩展名是图片但内容不是图片（或被截断）时 imread 返回 None，
    # 紧接着的 cvtColor 会抛 cv2.error 变成 500
    if image is None:
        raise ImageIdentificationError("图片无法读取，请确认上传的是有效的图片文件")

    # 转化为灰度图像
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 二值化
    # 固定阈值 150 会把亮于 150 的像素整片抹掉，于是浅色背景（浅灰纸、浅桌上的白纸）
    # 一条横线都留不下来；Otsu 从直方图自适应取阈值，深墨线/白纸的既有结果不变
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 使用形态学操作来连接线条的两侧
    kernel = np.ones((5,5),np.uint8)
    dilated = cv2.dilate(binary, kernel, iterations = 1)
    eroded = cv2.erode(dilated, kernel, iterations = 1)
    
    # 边缘检测
    edges = cv2.Canny(eroded, 50, 150, apertureSize=3)

    # 直线检测
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)

    # 整页没有可识别直线时 HoughLinesP 返回 None。这里不能退化成全 0：
    # 前端拿到 0 会当成真实边距去覆盖用户的参数框，再弹一个假的成功提示。
    # 交给调用方提示用户手动填写，用户填好的值原样保留。
    if lines is None:
        raise ImageIdentificationError("未识别到横线，请手动填写边距")

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

    # 二值化（同上，用 Otsu 以适应浅色背景）
    _, binary_rotated = cv2.threshold(gray_rotated, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 边缘检测
    edges_rotated = cv2.Canny(binary_rotated, 50, 150, apertureSize=3)

    # 直线检测
    lines_rotated = cv2.HoughLinesP(edges_rotated, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)

    # 旋转后同样可能一条直线都找不到，处理方式与上面一致
    if lines_rotated is None:
        raise ImageIdentificationError("未识别到横线，请手动填写边距")

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

    # 行距是必填结果：只有一条线、或相邻线间距都 <= 5px 时 distances 为空，
    # get_avg_distance([]) 会退回 0，前端又拿 0 去覆盖用户的行距——和「找不到线」
    # 是同一个坑。四周空白返回 0 可能是合法结果（内容铺满整页），所以只对行距判空。
    if not distances:
        raise ImageIdentificationError("未识别到横线，请手动填写边距")

    avg_distance = get_avg_distance(distances)
    print('左边平均空白长度：', avg_l_whitespace)
    print('右边平均空白长度：', avg_r_whitespace)
    print('平均行间距：', avg_distance)
    
    avg_l_whitespace = round(avg_l_whitespace)
    avg_r_whitespace = round(avg_r_whitespace)
    avg_t_whitespace = round(avg_t_whitespace)
    avg_b_whitespace = round(avg_b_whitespace)
    avg_distance = round(avg_distance)
    
    return avg_l_whitespace, avg_r_whitespace, avg_t_whitespace, avg_b_whitespace, avg_distance

if __name__ == '__main__':
    identify_distance('notebook.jpg')
import cv2
from PIL import Image
import pandas as pd
import glob
# Static Variables

init_path = ''

path_list = glob.glob(f'{init_path}images/*jpg')
static_width = 700
static_hight = 900
student_number_section_x = (285, 645)
green = (0, 255, 0)
yellow = (0, 255, 255)
red = (0, 0, 255)
padding = 6
column_distance = 100
option_distance = 20
initial_distance = 50
correct_answers = list([i%4 for i in range(50)] for _ in range(3)) + list([-1 for i in range(50)] for _ in range(3)) # The master answer
question_count = 100
scores = {"student_number": [],
          "correct_answer": [],
          "wrong_answer": [],
          "unanswered": [],
          "score": []}
paper_count = 1
# Load IMG
image_list = []
for path in path_list:
    image_list.append(cv2.imread(path))

image = image_list[0]
# Resize
dim = (static_width, static_hight)
for i in range(len(image_list)):
    image_list[i] = cv2.resize(image_list[i], dim, interpolation= cv2.INTER_AREA)

# Show the Image
def show_img(image):
    cv2.imshow('lol', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Draw centers 
def draw_centers(image, t):
    for i in t:
        center = find_center(i)
        cv2.circle(image, center, 2, green, -1)

# Do initial Prosessing
def img_init_pros(image):
    # initial prosessing
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur_image = cv2.GaussianBlur(gray_image, (3, 5), cv2.BORDER_DEFAULT)
    bin_img = cv2.threshold(blur_image, 130, 255, cv2.THRESH_BINARY_INV)[1]
    return bin_img
    
# Find the Center of contours
def find_center(contour):
    M = cv2.moments(contour)
    if M['m00'] != 0:
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])
        return (cx, cy)
    else: return (-1, -1)

# Find Sides
def find_sides(bin_img) -> list:
   # Find contoiurs
    l_contours = []
    l_cordinates = []
    r_contours = []
    r_cordinates = []
    all_contours = cv2.findContours(bin_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
    for c in all_contours:
        x, y = find_center(c)
        if (x < 45 and x > 5) and (y < static_hight - 30):
            l_contours.append(c)
            l_cordinates.append((x, y))
        elif (x < 690 and x > 670) and (y < static_hight - 30):
            r_contours.append(c)
            r_cordinates.append((x, y))

    return (l_contours, l_cordinates, r_contours, r_cordinates)

# Find the Student Number
def find_st_number(bin_img, left_first_10_line_y, right_first_10_line_y) -> str:
    all_contours= cv2.findContours(bin_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
    contours = []
    for c in all_contours:
        x, y = find_center(c)
        if (x < student_number_section_x[1] and x > student_number_section_x[0]) and (y > 77 and y < 205) and (cv2.contourArea(c) < 200 and cv2.contourArea(c) > 100):
            contours.append((c, x, y))
    student_number = ''
    contours = sorted(contours, key=lambda x: x[1]) # Making sure the contours are sorted correcl
    for c in contours:
        cv2.drawContours(image, [c[0]], -1, green, 0) # Debug
        for i in range(10):
            line = (left_first_10_line_y[i][1] + right_first_10_line_y[i][1])/2
            line_range = (line - padding, line + padding)
            if (c[2] > line_range[0] and c[2] < line_range[1]):
                student_number = student_number + str(i)
                break
    return student_number

# Find the filled bubbles
def find_filled_bubbles(bin_img, left_cordinates, right_cordinates) -> list:
    all_contours = cv2.findContours(bin_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
    contours = []
    for c in all_contours:
        x, y = find_center(c)
        if (x > 44 and x < 640) and (y > 210 and y < 868) and (cv2.contourArea(c) > 20):
            contours.append(c)
    answers = []
    answers_location = []
    for i in range(6):
        beggining = initial_distance + (i * column_distance)
        answers.append([])
        answers_location.append([])
        range_x:int
        range_y:int
        for j in range(50):
            answers[i].append([0, 0, 0, 0])
            answers_location[i].append([])
            line = (left_cordinates[j][1] + right_cordinates[j][1])/2
            range_y = (line - padding, line + padding)
            for k in range(4):
                range_x = (beggining + (k * option_distance), beggining + ((k + 1) * option_distance))
                for c in contours:
                    x, y = find_center(c)
                    if (x > range_x[0] and x < range_x[1]) and (y > range_y[0] and y < range_y[1]):
                        answers[i][j][k] = 1
                        answers_location[i][j] = [x, y]
                        break
            if not answers_location[i][j]:
                answers_location[i][j] = [(range_x[0]+range_x[1])/2, (range_y[0]+range_y[1])/2]
    return (answers, answers_location)

# Extract answer
def extract_st_answer(student_answer) -> int:
    answer:int
    for i in range(4):
        if student_answer[i] == 1:
            answer = i
            for j in range(3-i):
                if student_answer[j + i + 1] == 1:
                    return -1
            return answer
    return -1
    
# Mark a Question
def mark_question(image, student_answer, student_answer_location, correct_answer):
    student_answer = extract_st_answer(student_answer)
    color = green
    if correct_answer == -1: return 2
    elif student_answer == -1 : color = yellow
    elif student_answer != correct_answer: color = red

    if student_answer == -1:
        shift = (correct_answer - 3) * option_distance
    else:
        shift = (correct_answer - student_answer) * option_distance
    location = (int(shift + student_answer_location[0]), int(student_answer_location[1]))
    cv2.circle(image, location, 5, color, -1) 
    if color == green: return 1
    elif color == yellow: return -1
    else: return 0
    
# Mark a test paper
def mark_paper(image, st_answers, st_answer_location, correct_answers) -> Image:
    correct_count = 0
    wrong_count = 0
    unAnswered_count = 0
    score = 0
    st_results = {"Question": [],
                 "Correct_answer": [],
                 "Student_answer": [],
                 "Correct": []}

    for j in range(6):
        for i in range(50):
            result = mark_question(image, st_answers[j][i], st_answer_location[j][i], correct_answers[j][i]) # In case didn't work, make this function return the image itself.
            if result != 2:
                st_results["Question"].append((50*j + i))
                st_results["Correct_answer"].append(correct_answers[j][i])
                st_results["Student_answer"].append(extract_st_answer(st_answers[j][i]))
                st_results["Correct"].append(bool(result == 1))
            match result:
                case 1:
                    correct_count += 1
                case 0:
                    wrong_count += 1
                case -1:
                    unAnswered_count += 1
    
    score = correct_count - wrong_count/4
                    
    return [image, correct_count, wrong_count, unAnswered_count, score], st_results

def add_result_to_dict(st_number: int, result_list: list):
    scores["student_number"].append(st_number)
    scores["correct_answer"].append(result_list[0])
    scores["wrong_answer"].append(result_list[1])
    scores["unanswered"].append(result_list[2])
    scores["score"].append(result_list[3])
# Main Loop
for i in image_list:
    image = i
    # show_img(image)
    bin_img = img_init_pros(image)
    l_contours, l_cordinates, r_contours, r_cordinates = find_sides(bin_img)

    l_cordinates = sorted(l_cordinates, key=lambda x: x[1])
    r_cordinates = sorted(r_cordinates, key=lambda x: x[1])

    answers, ans_location = find_filled_bubbles(bin_img, l_cordinates[10:61], r_cordinates[10:61])
    st_number = find_st_number(bin_img, l_cordinates[0:10], r_cordinates[0:10])
    result_list, st_results = mark_paper(image, answers, ans_location, correct_answers)
    add_result_to_dict(st_number, result_list[1:])
    df = pd.DataFrame(st_results)
    df.to_excel(f'{init_path}individual_reports/{str(st_number)}_report.xlsx', index=False)
    cv2.imwrite(f'{init_path}marked_images/{str(st_number)}_paper.jpg', image)

   

pd.DataFrame(scores).to_excel(f'{init_path}summary/summary_report.xlsx', index=False)









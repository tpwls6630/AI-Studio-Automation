import os
import json
import csv
from collections import Counter

# solutions 폴더 경로 (절대 경로로 지정)
# 사용자의 실제 환경에 맞게 이 경로를 수정해야 할 수 있습니다.
SOLUTIONS_DIR = os.path.abspath("solutions")
OUTPUT_CSV_FILE = "tag_frequencies.csv"

def analyze_tags_in_json_files(solutions_dir, output_csv_file):
    """
    지정된 폴더 내의 모든 JSON 파일에서 '태그' 정보를 추출하고,
    각 태그의 빈도를 계산하여 CSV 파일로 저장합니다.
    """
    all_tags = []
    
    if not os.path.isdir(solutions_dir):
        print(f"오류: '{solutions_dir}' 폴더를 찾을 수 없습니다.")
        return

    print(f"'{solutions_dir}' 폴더에서 JSON 파일 검색 중...")
    for filename in os.listdir(solutions_dir):
        if filename.endswith(".json"):
            file_path = os.path.join(solutions_dir, filename)
            print(f"처리 중인 파일: {filename}")
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # JSON 데이터가 리스트 형태이고, 각 요소가 딕셔너리라고 가정
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and "tag" in item:
                                all_tags.append(item["tag"])
                            else:
                                print(f"경고: {filename} 파일의 '{item}' 항목에서 'tag'를 찾을 수 없거나 형식이 다릅니다.")
                    else:
                        print(f"경고: {filename} 파일의 최상위 데이터가 리스트 형태가 아닙니다.")
            except json.JSONDecodeError:
                print(f"오류: {filename} 파일이 유효한 JSON 형식이 아닙니다.")
            except Exception as e:
                print(f"'{filename}' 파일 처리 중 오류 발생: {e}")
                
    if not all_tags:
        print("분석할 태그를 찾지 못했습니다.")
        return
        
    print(f"총 {len(all_tags)}개의 태그를 추출했습니다.")
    
    # 태그 빈도 계산
    tag_counts = Counter(all_tags)
    
    print(f"'{output_csv_file}' 파일에 태그 빈도 저장 중...")
    try:
        with open(output_csv_file, 'w', newline='', encoding='utf-8-sig') as csvfile: # utf-8-sig로 Excel에서 한글 깨짐 방지
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(["태그", "빈도"]) # 헤더 작성
            for tag, count in tag_counts.most_common(): # 빈도가 높은 순으로 정렬
                csv_writer.writerow([tag, count])
        print(f"성공적으로 '{output_csv_file}' 파일에 태그 빈도를 저장했습니다.")
    except IOError:
        print(f"오류: '{output_csv_file}' 파일을 쓰는 데 실패했습니다.")
    except Exception as e:
        print(f"CSV 파일 저장 중 오류 발생: {e}")

if __name__ == "__main__":
    analyze_tags_in_json_files(SOLUTIONS_DIR, OUTPUT_CSV_FILE) 
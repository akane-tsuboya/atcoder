#!/usr/bin/env python
# coding: utf-8

# python3 fetch_submission.py abc???

# import
import requests
import os
import sys
import re
import html
import chromedriver_binary
from selenium import webdriver
from selenium.webdriver.common.by import By
from time import sleep
import git
import datetime



# APIを用いた提出データの取得
def getSubmissionData(userID):
    api_url = api_path + userID
    response = requests.get(api_url)
    jsonData = response.json()
    return jsonData

# 各問題において最も新しいAC提出のみを取得する
# 各コンテストごとにまとめて返す
def collectNewestAcceptedSubmissions(submissions):
    sortedData = sorted(submissions, key=lambda x: x['id'])  # IDで昇順ソートすると古い順になる
    submits = {} # 各問題ごとに最新の提出に更新する
    for data in sortedData:
        if data["result"] != "AC": # ACだった提出だけ対象
            continue
        submits[data["problem_id"]] = data
    
    result = {} # コンテストごとにまとめる
    for sub in submits.values():
        if not sub["contest_id"] in result:
            result[sub["contest_id"]] = []
        result[sub["contest_id"]].append(sub)
    return result

args = sys.argv
submit_name = args[1]
userID = "minamiA" #AtCoder username
api_path = "https://kenkoooo.com/atcoder/atcoder-api/results?user="
root = "submissions/"

submissions = getSubmissionData(userID)
submissions[:2]

newestSubmits =  collectNewestAcceptedSubmissions(submissions)
newestSubmits[submit_name][0]

# 保存用ディレクトリ作成
for contestName in newestSubmits:
    path = root + contestName
    os.makedirs(path, exist_ok=True)

add_cnt = 0
driver = webdriver.Chrome()
for submissions in newestSubmits.values():
    for sub in submissions:
        # 問題番号の取得
        problem_num = sub["problem_id"][-1]
        
        # 古い問題の場合には数字になっているので、アルファベットに戻す
        if problem_num.isdigit():
            problem_num = chr(int(problem_num)+ord('a')-1)
        
        # 作成するファイルへのパス
        path = root + sub["contest_id"] + "/" + problem_num
        # 拡張子の設定（Pythonのみ）
        if "Python" in sub["language"]:
            path += ".py"
        
        # 既に提出コードがある場合は取得せず、次の問題の提出を探す
        if os.path.isfile(path): continue
        
        # 提出ページへアクセス
        sub_url = "https://atcoder.jp/contests/" + sub["contest_id"] + "/submissions/" + str(sub["id"])
        driver.get(sub_url)
        
        # 提出コードの取得
        code = driver.find_element(By.ID,"submission-code") 
        
        # code.text は提出時に含めていない空白が期待に反して含まれてしまう
        # 空白はシンタックスハイライティングによるものであるように見える
        # innerHTML から不要なタグなどを消し、空白が意図通りのテキストを得る
        inner_html = code.get_attribute('innerHTML')
        list_items = re.findall(r'<li[^>]*>.*?</li>', inner_html)
        lines = []
        for li in list_items:
            line1 = re.sub(r'<[^>]+>', '', li)
            line2 = re.sub(r'&nbsp;', '', line1)
            line3 = html.unescape(line2)
            lines.append(line3 + "\n")
        code_text = ''.join(lines)
            
        # 書き込み
        with open(path, 'w') as f:
            f.write(code_text)
        
        # 追加したファイルの数を増やす
        add_cnt += 1
            
        # アクセス負荷軽減のために時間をおく(3秒)
        sleep(3)
        
driver.quit()




# git push
if add_cnt == 0:
    # 何も追加していなければGitにアクセスしない
    print("No added submissions, end process")
else:
    dt_now = datetime.datetime.now()
    repo_url = "https://github.com/akane-minami/atcoder.git"
    repo = git.Repo()
    repo.git.add("submissions/*")
    repo.git.commit("submissions/*", message="add submission: " + dt_now.strftime('%Y/%m/%d %H:%M:%S'))
    repo.git.push("origin", "main")
    print(f"Finished process, added {add_cnt} files")


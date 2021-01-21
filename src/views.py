# Copyright 2020 The `Kumar Nityan Suman` (https://github.com/nityansuman/). All Rights Reserved.
#
#                     GNU GENERAL PUBLIC LICENSE
#                        Version 3, 29 June 2007
#  Copyright (C) 2007 Free Software Foundation, Inc. <http://fsf.org/>
#  Everyone is permitted to copy and distribute verbatim copies
#  of this license document, but changing it is not allowed.
# ==============================================================================


# Import packages
import os
import flask
import pandas as pd
import numpy as np
from datetime import datetime
from flask import render_template, request, session
from werkzeug.utils import secure_filename
from src import app
from src.objective import ObjectiveTest
from src.subjective import SubjectiveTest
from src.utils import relative_ranking, backup
from src.mcq import fetchMCQ
import src.utils as utils
import sqlite3 as sql

# Placeholders
global_answers = list()
mcq_list = []

@app.route('/',methods=['GET', 'POST'])
def demo():
    tests = utils.FetchTests()

    return render_template("homepage.html", tests = tests)





@app.route('/home')
def home():
    ''' Renders the home page '''
    directory = os.path.join(str(os.getcwd()), "database")
    session["database_path"] = os.path.join(str(os.getcwd()), "database", "userlog.csv")

    if "userlog.csv" not in os.listdir(directory):
        df = pd.DataFrame(columns=["DATE", "USERNAME", "SUBJECT", "SUBJECT_ID", "TEST_TYPE", "TEST_ID", "SCORE", "RESULT"])
        df.to_csv(session["database_path"], index=False)
    else:
        print("Database in place!")

    session["date"] = datetime.now()
    return render_template(
        "index.html",
        date=session["date"].day,
        month=session["date"].month,
        year=session["date"].year
    )


@app.route("/form", methods=['GET', 'POST'])
def form():
    ''' Prompt user to start the test '''
    if request.form["username"] == "":
        session["username"] = "Username"
    else:
        session["username"] = request.form["username"]
    return render_template(
        "form.html",
        username=session["username"]
    )


@app.route("/generate_test", methods=["GET", "POST"])
def generate_test():
    session["subject_id"] = request.form["subject_id"]
    if session["subject_id"] == "0":
        session["subject_name"] = "SOFTWARE ENGINEERING"
        session["filepath"] = os.path.join(str(os.getcwd()), "corpus", "software-testing.txt")
    elif session["subject_id"] == "1":
        session["subject_name"] = "DBMS"
        session["filepath"] = os.path.join(str(os.getcwd()), "corpus", "dbms.txt")
    elif session["subject_id"] == "2":
        session["subject_name"] = "Machine Learning"
        session["filepath"] = os.path.join(str(os.getcwd()), "corpus", "ml.txt")
    elif session["subject_id"] == "99":
        file = request.files["file"]
        session["filepath"] = secure_filename(file.filename)
        file.save(secure_filename(file.filename))
        session["subject_name"] = "CUSTOM"
    else:
        print("Done!")
    session["test_id"] = request.form["test_id"]

    if session["test_id"] == "0":
        # Generate objective test
        objective_generator = ObjectiveTest(session["filepath"])
        question_list, answer_list = objective_generator.generate_test()
        for ans in answer_list:
            global_answers.append(ans)
        
        return render_template(
            "objective_test.html",
            username=session["username"],
            testname=session["subject_name"],
            question1=question_list[0],
            question2=question_list[1],
            question3=question_list[2]
        )
    elif session["test_id"] == "1":
        # Generate subjective test
        subjective_generator = SubjectiveTest(session["filepath"])
        question_list, answer_list = subjective_generator.generate_test(num_of_questions=2)
        for ans in answer_list:
            global_answers.append(ans)
        
        return render_template(
            "subjective_test.html",
            username=session["username"],
            testname=session["subject_name"],
            question1=question_list[0],
            question2=question_list[1]
        )
    else:
        print("Done!")
        return None


@ app.route("/output", methods=["GET", "POST"])
def output():
    default_ans = list()
    user_ans = list()
    if session["test_id"] == "0":
        # Access objective answers
        user_ans.append(str(request.form["answer1"]).strip().upper())
        user_ans.append(str(request.form["answer2"]).strip().upper())
        user_ans.append(str(request.form["answer3"]).strip().upper())
    elif session["test_id"] == "1":
        # Access subjective answers
        user_ans.append(str(request.form["answer1"]).strip().upper())
        user_ans.append(str(request.form["answer2"]).strip().upper())
    else:
        print("Done!")
    
    # Process answers
    for x in global_answers:
        default_ans.append(str(x).strip().upper())
    
    # Evaluate the user repsonse
    total_score = 0
    status = None
    if session["test_id"] == "0":
        # Evaluate objective answer
        for i, _ in enumerate(user_ans):
            if user_ans[i] == default_ans[i]:
                total_score += 100
        total_score /= 3
        total_score = round(total_score, 3)
        if total_score >= 33.33:
            status = "Pass"
        else:
            status = "Fail"
    elif session["test_id"] == "1":
        # evaluate subjective answer
        for i, _ in enumerate(default_ans):
            # Subjective test
            subjective_generator = SubjectiveTest(session["filepath"])
            total_score += subjective_generator.evaluate_subjective_answer(default_ans[i], user_ans[i])
        total_score /= 2
        total_score = round(total_score, 3)
        if total_score > 50.0:
            status = "Pass"
        else:
            status = "Fail"
    # Backup data
    session["score"] = np.round(total_score, decimals=2)
    session["result"] = status
    try:
        status = backup(session)
    except Exception as e:
        print("Exception raised at `views.__output`:", e)
    # Compute relative ranking of the student
    max_score, min_score, mean_score = relative_ranking(session)
    # Clear instance
    global_answers.clear()

    # Render output
    return render_template(
        "output.html",
        show_score=session["score"],
        username=session["username"],
        subjectname=session["subject_name"],
        status=session["result"],
        max_score=max_score,
        min_score=min_score,
        mean_score=mean_score
    )

@ app.route("/mcq/<name>", methods=["GET", "POST"])
def mcq(name):
    mcq_list = utils.FetchMCQfromDB(name)
    print(mcq_list)
    session['mcq_list'] = mcq_list
    return render_template(
        "mcq.html",
         mcq_list=mcq_list
    )

@app.route('/quiz', methods=['POST'])
def quiz_answers():
    mcq_list = utils.FetchMCQfromDB('dbms.txt')
    mark = 0
    for mcq in mcq_list:
        if request.form[mcq['question']] == mcq['answer']:
            mark += 1
    percentage = round((mark/len(mcq_list)), 2 ) * 100
    # return '<h1>Percentage: ' + str(percentage) + '%' + '</h1>'
    return render_template("results.html", percentage = percentage, correct_answers = mark)
        

@app.route('/upload', methods=["GET"])
def upload():
    return render_template("file_upload.html")

@app.route('/success', methods = ['POST'])  
def success():  
    if request.method == 'POST':  
        f = request.files['file']  
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], f.filename))  

        conn = sql.connect('database.db')
        conn.execute('CREATE TABLE IF NOT EXISTS mcqs(filename TEXT, question TEXT, answer TEXT, option1 TEXT, option2 TEXT, option3 TEXT, option4 TEXT)')

        # cur = conn.cursor()
    
        mcq_list = fetchMCQ("corpus/" + f.filename)
        # for mcq in mcq_list:
        #         cur.execute("INSERT INTO mcqs (filename, question, answer, option1, option2, option3, option4) VALUES (?,?,?,?,?,?,?)",(f.filename,mcq['question'],mcq['answer'],mcq['choices'][0],mcq['choices'][1],mcq['choices'][2],mcq['choices'][3]) )

        try:
            with sql.connect("database.db") as con:
                print(mcq_list)
                cur = con.cursor()
                for mcq in mcq_list:
                    print(mcq)
                    cur.execute("INSERT INTO mcqs (filename, question, answer, option1, option2, option3, option4) VALUES (?,?,?,?,?,?,?)",(f.filename,mcq['question'],mcq['answer'],mcq['choices'][0],mcq['choices'][1],mcq['choices'][2],mcq['choices'][3]) )
                con.commit()
                msg = "Record successfully added"
        except Exception as e:
            msg = str(e)
            con.rollback()         
        finally:
            con.close()
            return render_template("success.html", msg = msg)
            

    


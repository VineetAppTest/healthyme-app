
def map_answer(v):
    if v in [None,"","Select","NA"]: return 0
    try: return int(v)
    except: return 0
def completion(answers,total):
    answered=sum(1 for v in answers.values() if v in ["NA","1","2","3"])
    return answered, answered/total if total else 0
def unanswered_questions(questions,answers):
    return [q for q in questions if answers.get(q["code"],"Select")=="Select"]
def score_answers(answers):
    return {"total":sum(map_answer(v) for v in answers.values()),"all_na": bool(answers) and all(v=="NA" for v in answers.values())}

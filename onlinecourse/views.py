
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Course, Question, Choice, Submission, Learner


def course_details(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(
        request,
        "onlinecourse/course_details_bootstrap.html",
        {"course": course},
    )


def submit(request):
    if request.method != "POST":
        return HttpResponse("Please submit the exam using POST.")

    question_ids = request.POST.getlist("question_ids")
    score = 0
    total = len(question_ids)
    results = []

    for question_id in question_ids:
        question = get_object_or_404(Question, id=question_id)
        choice_id = request.POST.get("question_" + str(question_id))
        choice = None

        if choice_id:
            choice = Choice.objects.filter(
                id=choice_id, question=question
            ).first()

        correct = bool(choice and choice.is_correct)
        if correct:
            score += 1

        results.append({
            "question": question,
            "selected": choice,
            "correct": correct,
        })

    request.session["exam_score"] = score
    request.session["exam_total"] = total
    request.session["exam_results"] = [
        {
            "question": item["question"].text,
            "selected": item["selected"].text if item["selected"] else "Not answered",
            "correct": item["correct"],
        }
        for item in results
    ]

    return render(
        request,
        "onlinecourse/exam_result.html",
        {
            "score": score,
            "total": total,
            "results": results,
        },
    )


def show_exam_result(request):
    return render(
        request,
        "onlinecourse/exam_result.html",
        {
            "score": request.session.get("exam_score", 0),
            "total": request.session.get("exam_total", 0),
            "saved_results": request.session.get("exam_results", []),
        },
    )

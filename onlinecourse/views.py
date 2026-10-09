from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.urls import reverse
from .models import Course, Question, Choice, Submission, Learner


def course_details(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(
        request,
        "onlinecourse/course_details_bootstrap.html",
        {"course": course},
    )


def submit(request, course_id):
    if request.method != "POST":
        return HttpResponse("Please submit the exam using POST.")

    if not request.user.is_authenticated:
        return HttpResponse("Please log in before submitting the exam.")

    course = get_object_or_404(Course, id=course_id)
    learner, _ = Learner.objects.get_or_create(user=request.user)

    question_ids = request.POST.getlist("question_ids")
    if not question_ids:
        question_ids = list(
            Question.objects.filter(lesson__course=course)
            .values_list("id", flat=True)
        )

    submission_ids = []
    selected_ids = []

    for question_id in question_ids:
        question = get_object_or_404(
            Question,
            id=question_id,
            lesson__course=course,
        )

        choice_id = request.POST.get("question_" + str(question_id))
        choice = None

        if choice_id:
            choice = Choice.objects.filter(
                id=choice_id,
                question=question,
            ).first()

        submission = Submission.objects.create(
            learner=learner,
            question=question,
            choice=choice,
        )

        submission_ids.append(submission.id)

        if choice:
            selected_ids.append(choice.id)

    request.session["submission_ids"] = submission_ids
    request.session["selected_ids"] = selected_ids
    request.session["submission_course_id"] = course.id

    if not submission_ids:
        return HttpResponse("No questions are available for this course.")

    return redirect(
        reverse(
            "show_exam_result",
            kwargs={
                "course_id": course.id,
                "submission_id": submission_ids[-1],
            },
        )
    )


def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, id=course_id)

    if not request.user.is_authenticated:
        return HttpResponse("Please log in to view the exam result.")

    learner = get_object_or_404(Learner, user=request.user)

    # Ensure the requested submission belongs to this learner and course.
    get_object_or_404(
        Submission,
        id=submission_id,
        learner=learner,
        question__lesson__course=course,
    )

    submission_ids = request.session.get("submission_ids", [submission_id])

    submissions = Submission.objects.filter(
        id__in=submission_ids,
        learner=learner,
        question__lesson__course=course,
    )

    total_score = sum(
        submission.is_get_score() for submission in submissions
    )
    possible_score = submissions.count()

    selected_ids = request.session.get("selected_ids", [])
    grade = (
        round(total_score * 100 / possible_score)
        if possible_score else 0
    )

    return render(
        request,
        "onlinecourse/exam_result.html",
        {
            "course": course,
            "selected_ids": selected_ids,
            "grade": grade,
            "possible": possible_score,
            "score": total_score,
            "total": possible_score,
            "results": submissions,
        },
    )
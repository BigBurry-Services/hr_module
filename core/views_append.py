@hr_required
def toggle_no_break(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)
    attendance.no_break = not attendance.no_break
    attendance.save()
    
    # Redirect back to previous page
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('summary')

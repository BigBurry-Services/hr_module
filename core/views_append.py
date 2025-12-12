

@login_required
def sync_attendance_view(request):
    if request.method == 'POST':
        try:
            target_date_str = request.POST.get('date')
            if target_date_str:
                 target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d').date()
            else:
                 target_date = datetime.date.today()
            
            service = DeviceSyncService()
            results = service.sync_devices(target_date=target_date)
            
            if results['errors']:
                return JsonResponse({'status': 'warning', 'message': 'Sync completed with errors.', 'details': results}, status=200)
            
            return JsonResponse({'status': 'success', 'message': f"Successfully processed {results['processed_count']} records from {results['devices_connected']} devices."}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)

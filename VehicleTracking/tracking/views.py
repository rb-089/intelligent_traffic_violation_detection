import os
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from .models import Vehicle, OverspeedIncident
from .vehicle_detection import detect_vehicles
from django.contrib import messages
from .forms import IncidentReportForm
from django.db.models import Count
from .models import IncidentReport

# Configure logging
logger = logging.getLogger(__name__)

def upload_video(request):
    if request.method == 'POST' and 'video' in request.FILES:
        video_file = request.FILES['video']
        speed_limit = request.POST.get('speed_limit', 60)  # Default speed limit: 60 km/h

        # Validate speed limit
        try:
            speed_limit = float(speed_limit)
            if speed_limit <= 0 or speed_limit > 300:  # Reasonable range
                raise ValueError("Speed limit out of range.")
        except ValueError as e:
            logger.warning(f"Invalid speed limit: {speed_limit}")
            return JsonResponse({"status": "error", "message": "Invalid speed limit value."})

        # Save the uploaded video
        try:
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            sanitized_name = fs.get_available_name(video_file.name)
            video_path = fs.save(sanitized_name, video_file)
            video_full_path = os.path.join(settings.MEDIA_ROOT, video_path)
        except Exception as e:
            logger.error(f"Error saving video: {str(e)}")
            return JsonResponse({"status": "error", "message": "Error saving video."})

        try:
            # Define meters per pixel for speed calculation (calibrate for your setup)
            meters_per_pixel = 0.01  # Example calibration value
            detection_result = detect_vehicles(video_full_path, speed_limit, meters_per_pixel)

            if detection_result["status"] == "success":
                if not detection_result["data"]:  # No violations
                    return JsonResponse({
                        "status": "success",
                        "message": detection_result["message"]
                    })

                overspeeding_vehicles = detection_result["data"]

                # Save overspeeding incidents to the database
                with transaction.atomic():
                    for incident in overspeeding_vehicles:
                        vehicle_number = incident["vehicle_id"]
                        speed = incident["speed"]

                        try:
                            vehicle = Vehicle.objects.get(vehicle_number=vehicle_number)
                        except ObjectDoesNotExist:
                            logger.warning(f"Vehicle not found in database: {vehicle_number}")
                            continue

                        OverspeedIncident.objects.create(
                            vehicle=vehicle,
                            speed=speed,
                            location="Unknown",  # Update as needed
                            number_plate=vehicle_number,
                        )

                return JsonResponse({
                    "status": "success",
                    "message": detection_result["message"]
                })

        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            return JsonResponse({"status": "error", "message": "Error processing video."})
        finally:
            # Clean up video file
            try:
                if os.path.exists(video_full_path):
                    os.remove(video_full_path)
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up video file: {cleanup_error}")

    return render(request, 'upload_video.html')  # Render the upload form

from geopy.distance import geodesic

def group_nearby_locations(locations, range_in_meters=50):
    """
    Groups locations within a specified range.
    :param locations: List of dictionaries with 'location' and 'incident_count'.
    :param range_in_meters: Distance range in meters to group locations.
    :return: Grouped list of locations with aggregated incident counts.
    """
    grouped_locations = []

    for loc in locations:
        try:
            lat, lon = map(float, loc['location'].split(','))
        except ValueError:
            logger.warning(f"Invalid location format: {loc['location']}")
            continue

        current_point = (lat, lon)
        matched_group = None

        for group in grouped_locations:
            group_point = group['center']
            if geodesic(current_point, group_point).meters <= range_in_meters:
                matched_group = group
                break

        if matched_group:
            matched_group['incident_count'] += loc['incident_count']
            matched_group['locations'].append(loc['location'])
        else:
            grouped_locations.append({
                'center': current_point,
                'incident_count': loc['incident_count'],
                'locations': [loc['location']],
            })

    return grouped_locations
def report_incident(request):
    if request.method == 'POST':
        # Make a mutable copy of POST data to inject coordinates if needed
        post_data = request.POST.copy()

        # This ensures the 'location' field is passed to the form if needed
        location = post_data.get('location', '')
        if location:
            post_data['location'] = location  # Ensure it's present

        form = IncidentReportForm(post_data, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Your report has been submitted successfully.")
            return redirect('report_incident')
    else:
        form = IncidentReportForm()

    return render(request, 'report_incident.html', {'form': form})


def accident_rankings(request):
    # Fetch incidents and count per location
    incidents = (
        IncidentReport.objects.values('location')
        .annotate(incident_count=Count('id'))
    )
    
    # Group locations within 50 meters
    grouped_locations = group_nearby_locations(incidents)

    # Prepare rankings data
    rankings = [
        {
            'location': ', '.join(group['locations']),
            'incident_count': group['incident_count'],
        }
        for group in grouped_locations
    ]
    rankings.sort(key=lambda x: x['incident_count'], reverse=True)

    return render(request, 'accident_rankings.html', {'rankings': rankings})

def home(request):
    return render(request, 'home.html')

def contact_us(request):
    return render(request, 'contact.html')
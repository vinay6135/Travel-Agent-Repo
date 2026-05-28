import json
import boto3
import uuid
import os

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet

s3 = boto3.client("s3")

BUCKET_NAME = os.environ["S3_BUCKET_NAME"]

def lambda_handler(event, context):

    try:

        flight_details = event.get(
            "flight_details",
            "No flight details"
        )

        weather_details = event.get(
            "weather_details",
            "No weather details"
        )

        pdf_filename = f"travel-report-{uuid.uuid4()}.pdf"

        pdf_path = f"/tmp/{pdf_filename}"

        doc = SimpleDocTemplate(pdf_path)

        styles = getSampleStyleSheet()

        story = []

        story.append(
            Paragraph(
                "AI Travel Report",
                styles['Title']
            )
        )

        story.append(Spacer(1, 20))

        story.append(
            Paragraph(
                "<b>Flight Information</b>",
                styles['Heading2']
            )
        )

        story.append(
            Paragraph(
                flight_details,
                styles['BodyText']
            )
        )

        story.append(Spacer(1, 20))

        story.append(
            Paragraph(
                "<b>Weather Forecast</b>",
                styles['Heading2']
            )
        )

        story.append(
            Paragraph(
                weather_details,
                styles['BodyText']
            )
        )

        doc.build(story)

        s3.upload_file(
            pdf_path,
            BUCKET_NAME,
            pdf_filename
        )

        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': BUCKET_NAME,
                'Key': pdf_filename
            },
            ExpiresIn=3600
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "pdf_url": presigned_url
            })
        }

    except Exception as e:

        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e)
            })
        }
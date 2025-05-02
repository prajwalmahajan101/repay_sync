from django import forms

class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label='Select a CSV file',
        help_text='The CSV file should contain the following columns: customer_id, disposition, comment, next_call_date (optional). The next_call_date should be in YYYY-MM-DD HH:MM:SS format.'
    ) 
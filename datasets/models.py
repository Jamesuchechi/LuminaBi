from django.db import models
from django.conf import settings


class Dataset(models.Model):
	owner = models.ForeignKey(
		settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='datasets'
	)
	name = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	file = models.FileField(upload_to='datasets/originals/')
	cleaned_file = models.FileField(upload_to='datasets/cleaned/', blank=True, null=True)
	uploaded_at = models.DateTimeField(auto_now_add=True)
	row_count = models.IntegerField(null=True, blank=True)
	col_count = models.IntegerField(null=True, blank=True)
	metadata = models.JSONField(default=dict, blank=True)
	is_cleaned = models.BooleanField(default=False)

	class Meta:
		ordering = ['-uploaded_at']

	def __str__(self):
		return f"{self.name} ({self.owner})"

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created = models.DateTimeField(auto_created=True)
    deleted = models.BooleanField(default=False)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text}- read :{self.read} from : {self.sender}"


class Chat(models.Model):
    participants = models.ManyToManyField(User)
    name = models.CharField(max_length=200, blank=True)
    group = models.BooleanField(default=False)
    messages = models.ManyToManyField(Message, blank=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} {self.name} - group: {self.group}"

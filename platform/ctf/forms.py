from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

SMART_INCIDENT_SLUG = "nova-systems-smart-incident-estimator"


SMART_INCIDENT_RUBRIC = {
    "visualization_score": ("Compréhension du problème /10", 10),
    "interpretation_score": ("Type d'apprentissage /10", 10),
    "cleaning_score": ("Analyse du dataset /10", 10),
    "feature_engineering_score": ("Régression linéaire /20", 20),
    "model_performance_score": ("Exactitude des prédictions /10", 10),
    "error_analysis_score": ("Pseudo-code /15", 15),
    "submission_quality_score": ("Maquette web, réseau et limites /20", 20),
    "presentation_score": ("Présentation et travail d'équipe /5", 5),
}

DEFAULT_HACKATHON_RUBRIC = {
    "visualization_score": ("Visualisations /150", 150),
    "interpretation_score": ("Interprétation /100", 100),
    "cleaning_score": ("Nettoyage /100", 100),
    "feature_engineering_score": ("Préparation variables /150", 150),
    "model_performance_score": ("Performance modèle /250", 250),
    "error_analysis_score": ("Analyse erreurs /100", 100),
    "submission_quality_score": ("Qualité submission.csv /50", 50),
    "presentation_score": ("Présentation /100", 100),
}


def hackathon_rubric(event=None):
    if event and event.slug == SMART_INCIDENT_SLUG:
        return SMART_INCIDENT_RUBRIC
    return DEFAULT_HACKATHON_RUBRIC


def hackathon_score_max(event=None):
    return sum(max_value for _, max_value in hackathon_rubric(event).values())


from .models import Team


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(label="Prénom", max_length=150)
    last_name = forms.CharField(label="Nom", max_length=150)
    email = forms.EmailField(label="Email")

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Un compte existe déjà avec cet email.")
        return email


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Email", widget=forms.EmailInput(attrs={"autofocus": True}))


class TeamCreateForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ("name",)
        labels = {"name": "Nom de la team"}


class JoinTeamForm(forms.Form):
    team_id = forms.IntegerField(widget=forms.HiddenInput)


class SubmissionForm(forms.Form):
    flag = forms.CharField(label="Flag", max_length=255, widget=forms.TextInput(attrs={"placeholder": "DIC{...}"}))


class BonusSubmissionForm(forms.Form):
    flag = forms.CharField(
        label="Flag bonus",
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "DIC{fragment1_fragment2_fragment3_fragment4_fragment5}"}),
    )


class EventStartForm(forms.Form):
    duration_minutes = forms.IntegerField(
        label="Durée en minutes",
        min_value=1,
        initial=120,
        widget=forms.NumberInput(attrs={"min": "1"}),
    )


class AdminTeamCreateForm(forms.Form):
    name = forms.CharField(label="Nom de la team", max_length=80)
    captain_id = forms.IntegerField(required=False, widget=forms.HiddenInput)


class AdminMemberForm(forms.Form):
    user_id = forms.IntegerField(widget=forms.HiddenInput)


class HackathonSubmissionForm(forms.Form):
    notebook = forms.FileField(label="Notebook Jupyter (.ipynb)")
    prediction_file = forms.FileField(label="Fichier de soumission (.csv)")
    presentation = forms.FileField(label="Présentation (.pdf)")
    notes = forms.CharField(label="Notes pour le jury", required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event
        if event and event.slug == SMART_INCIDENT_SLUG:
            self.fields["notebook"].label = "Archive finale de l'équipe (.zip)"
            self.fields.pop("prediction_file")
            self.fields["presentation"].label = "Support de présentation optionnel (.pdf)"
            self.fields["presentation"].required = False
            self.fields["notes"].label = "Notes pour le jury"

    def clean_notebook(self):
        file = self.cleaned_data["notebook"]
        if self.event and self.event.slug == SMART_INCIDENT_SLUG:
            if not file.name.lower().endswith(".zip"):
                raise forms.ValidationError("Le livrable final doit être une archive .zip.")
        elif not file.name.lower().endswith(".ipynb"):
            raise forms.ValidationError("Le notebook doit être un fichier .ipynb.")
        return file

    def clean_prediction_file(self):
        file = self.cleaned_data["prediction_file"]
        if not file:
            return file
        if self.event and self.event.slug == SMART_INCIDENT_SLUG:
            if not file.name.lower().endswith((".pdf", ".png", ".jpg", ".jpeg")):
                raise forms.ValidationError("L'annexe doit être un .pdf, .png, .jpg ou .jpeg.")
            return file
        if not file.name.lower().endswith(".csv"):
            raise forms.ValidationError("Le fichier de soumission doit être un .csv.")
        return file

    def clean_presentation(self):
        file = self.cleaned_data["presentation"]
        if not file:
            return file
        if not file.name.lower().endswith(".pdf"):
            raise forms.ValidationError("La présentation doit être un fichier .pdf.")
        return file


class HackathonScoreForm(forms.Form):
    visualization_score = forms.IntegerField(min_value=0)
    interpretation_score = forms.IntegerField(min_value=0)
    cleaning_score = forms.IntegerField(min_value=0)
    feature_engineering_score = forms.IntegerField(min_value=0)
    model_performance_score = forms.IntegerField(min_value=0)
    error_analysis_score = forms.IntegerField(min_value=0)
    submission_quality_score = forms.IntegerField(min_value=0)
    presentation_score = forms.IntegerField(min_value=0)
    jury_feedback = forms.CharField(label="Feedback jury", required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, (label, max_value) in hackathon_rubric(event).items():
            self.fields[field_name].label = label
            self.fields[field_name].max_value = max_value
            self.fields[field_name].widget.attrs.update({"min": "0", "max": str(max_value)})




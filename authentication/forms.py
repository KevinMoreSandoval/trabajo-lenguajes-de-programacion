from django import forms

from .models import Rol, Usuario


class UsuarioBaseForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = (
            'first_name',
            'last_name',
            'username',
            'email',
            'dni',
            'telefono',
            'fecha_nacimiento',
            'rol',
            'activo',
        )
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rol'].queryset = Rol.objects.filter(nombre__in=Rol.ROLES_VALIDOS).order_by('nombre')


class UsuarioCreateForm(UsuarioBaseForm):
    password = forms.CharField(
        label='Contrasena',
        widget=forms.PasswordInput,
        min_length=8,
    )
    confirm_password = forms.CharField(
        label='Confirmar contrasena',
        widget=forms.PasswordInput,
        min_length=8,
    )

    class Meta(UsuarioBaseForm.Meta):
        fields = UsuarioBaseForm.Meta.fields + ('password', 'confirm_password')

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', 'Las contrasenas no coinciden.')
        return cleaned_data

    def save(self, commit=True):
        password = self.cleaned_data.pop('password')
        self.cleaned_data.pop('confirm_password', None)
        user = super().save(commit=False)
        user.set_password(password)
        self._sync_staff_flags(user)
        if commit:
            user.save()
        return user

    def _sync_staff_flags(self, user):
        rol_nombre = user.rol.nombre if user.rol else Rol.CLIENTE
        user.is_staff = rol_nombre in (Rol.ADMIN, Rol.RECEPCIONISTA)
        user.is_superuser = rol_nombre == Rol.ADMIN


class UsuarioUpdateForm(UsuarioBaseForm):
    password = forms.CharField(
        label='Nueva contrasena',
        widget=forms.PasswordInput,
        required=False,
        min_length=8,
        help_text='Dejalo vacio para mantener la contrasena actual.',
    )

    class Meta(UsuarioBaseForm.Meta):
        fields = UsuarioBaseForm.Meta.fields + ('password',)

    def save(self, commit=True):
        password = self.cleaned_data.pop('password', '')
        user = super().save(commit=False)
        if password:
            user.set_password(password)
        rol_nombre = user.rol.nombre if user.rol else Rol.CLIENTE
        user.is_staff = rol_nombre in (Rol.ADMIN, Rol.RECEPCIONISTA)
        user.is_superuser = rol_nombre == Rol.ADMIN
        if commit:
            user.save()
        return user


class ClienteRecepcionForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = (
            'first_name',
            'last_name',
            'dni',
            'email',
            'telefono',
            'fecha_nacimiento',
        )
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }

    def save(self, commit=True):
        cliente = super().save(commit=False)
        rol, _ = Rol.objects.get_or_create(nombre=Rol.CLIENTE)
        cliente.rol = rol
        cliente.username = cliente.username or cliente.email or cliente.dni
        cliente.activo = True
        cliente.is_staff = False
        cliente.is_superuser = False
        if not cliente.password:
            cliente.set_unusable_password()
        if commit:
            cliente.save()
        return cliente

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.usuario import Usuario
from schemas.usuario import UsuarioLogin, UsuarioCreate
from utils.security import verify_password, create_access_token, hash_password
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from utils.security import SECRET_KEY, ALGORITHM
from schemas.usuario import UsuarioUpdate
from schemas.usuario import ChangePassword

router = APIRouter(prefix="/auth", tags=["Auth"])

# OAuth2 para Swagger Authorize
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ---------------- OBTENER USUARIO ACTUAL ----------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")

    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario = db.query(Usuario).filter(
        Usuario.username == username
    ).first()

    if usuario is None:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Usuario desactivado")

    return usuario


# ---------------- REQUERIR ROL ----------------
def require_role(role: str):
    def role_checker(
        current_user: Usuario = Depends(get_current_user)
    ):
        if current_user.rol != role:
            raise HTTPException(status_code=403, detail="No autorizado")
        return current_user
    return role_checker


# ---------------- LOGIN (COMPATIBLE SWAGGER + FLUTTER) ----------------
@router.post("/login")
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Este login es compatible con Swagger Authorize
    (OAuth2 password flow)
    """

    usuario = db.query(Usuario).filter(
        Usuario.username == form_data.username
    ).first()

    if not usuario or not verify_password(form_data.password, usuario.password):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Usuario desactivado")

    token = create_access_token({
        "sub": usuario.username,
        "rol": usuario.rol
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "rol": usuario.rol
    }


# ---------------- LOGIN JSON (PARA FLUTTER) ----------------
@router.post("/login-json")
def login_json(datos: UsuarioLogin, db: Session = Depends(get_db)):
    """
    Este endpoint acepta JSON normal.
    Útil para Flutter.
    """
    print(f"🔐 1 - Iniciando login para usuario: {datos.username}")
    
    try:
        print(f"🔐 2 - Intentando consultar usuario en BD...")
        usuario = db.query(Usuario).filter(
            Usuario.username == datos.username
        ).first()
        
        print(f"🔐 3 - Usuario encontrado: {usuario is not None}")
        
        if not usuario:
            print(f"❌ Usuario NO encontrado: {datos.username}")
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
        
        print(f"🔐 4 - Usuario encontrado: {usuario.username}, verificando contraseña...")
        password_valid = verify_password(datos.password, usuario.password)
        print(f"🔐 5 - Contraseña válida: {password_valid}")
        
        if not password_valid:
            print(f"❌ Contraseña incorrecta para: {datos.username}")
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        if not usuario.activo:
            print(f"❌ Usuario inactivo: {datos.username}")
            raise HTTPException(status_code=403, detail="Usuario desactivado")

        print(f"🔐 6 - Generando token para: {datos.username}")
        token = create_access_token({
            "sub": usuario.username,
            "rol": usuario.rol
        })
        
        print(f"✅ Login exitoso para: {datos.username}")
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "rol": usuario.rol
        }
    except Exception as e:
        print(f"❌ Error en login: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e


# ---------------- REGISTER ----------------
@router.post("/register")
def register(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    existe = db.query(Usuario).filter(
        Usuario.username == usuario.username
    ).first()

    if existe:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    existe_email = db.query(Usuario).filter(
        Usuario.email == usuario.email
    ).first()

    if existe_email:
        raise HTTPException(status_code=400, detail="El email ya existe")

    nuevo = Usuario(
        username=usuario.username,
        password=hash_password(usuario.password),
        rol=usuario.rol,
        activo=True,
        email=usuario.email,
        telefono=usuario.telefono
    )

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return {"mensaje": "Usuario creado correctamente"}


# ---------------- USUARIO ACTUAL ----------------
@router.get("/me")
def obtener_usuario_actual(
    current_user: Usuario = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "rol": current_user.rol,
        "activo": current_user.activo,
        "email": current_user.email,
        "telefono": current_user.telefono
    }


# ---------------- ACTUALIZAR PERFIL ----------------
@router.patch("/usuarios/{usuario_id}")
def actualizar_usuario(
    usuario_id: int,
    datos: UsuarioUpdate,
    db: Session = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user)
):
    # Solo puede editarse a sí mismo o ser admin
    if usuario_actual.id != usuario_id and usuario_actual.rol != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")

    # Buscar usuario
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # Si no manda nada
    if datos.email is None and datos.telefono is None:
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar al menos un campo para actualizar"
        )

    # ---------------- EMAIL ----------------
    if datos.email is not None:
        existe_email = db.query(Usuario).filter(
            Usuario.email == datos.email
        ).first()

        if existe_email and existe_email.id != usuario_id:
            raise HTTPException(status_code=400, detail="Email ya registrado")

        usuario.email = datos.email

    # ---------------- TELEFONO ----------------
    if datos.telefono is not None:
        usuario.telefono = datos.telefono

    db.commit()
    db.refresh(usuario)

    return {
        "mensaje": "Perfil actualizado correctamente",
        "usuario": {
            "id": usuario.id,
            "username": usuario.username,
            "rol": usuario.rol,
            "activo": usuario.activo,
            "email": usuario.email,
            "telefono": usuario.telefono
        }
    }

# ---------------- CAMBIAR CONTRASEÑA ----------------
@router.patch("/cambiar-password")
def cambiar_password(
    datos: ChangePassword,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar contraseña actual
    if not verify_password(datos.password_actual, current_user.password):
        raise HTTPException(status_code=400, detail="Contraseña actual incorrecta")

    # (Opcional pero recomendado)
    if datos.password_actual == datos.nueva_password:
        raise HTTPException(status_code=400, detail="La nueva contraseña no puede ser igual")

    # Guardar nueva contraseña
    current_user.password = hash_password(datos.nueva_password)

    db.commit()
    db.refresh(current_user)

    return {"mensaje": "Contraseña actualizada correctamente"}
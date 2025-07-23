# Cibozer Project Refactoring Plan

## Nueva Estructura de Directorios

```
cibozer/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models/              # Database models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── payment.py
│   │   ├── meal_plan.py
│   │   └── usage.py
│   ├── routes/              # Route blueprints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── main.py
│   │   ├── admin.py
│   │   ├── payment.py
│   │   └── share.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   ├── meal_optimizer.py
│   │   ├── video_generator.py
│   │   ├── pdf_generator.py
│   │   └── payment_processor.py
│   ├── core/                # Core functionality
│   │   ├── __init__.py
│   │   ├── nutrition_data.py
│   │   ├── meal_algorithms.py
│   │   └── video_core.py
│   ├── utils/               # Utilities
│   │   ├── __init__.py
│   │   ├── security.py
│   │   ├── validators.py
│   │   ├── decorators.py
│   │   └── helpers.py
│   └── extensions.py        # Flask extensions
├── config/
│   ├── __init__.py
│   ├── default.py
│   ├── development.py
│   ├── production.py
│   └── testing.py
├── migrations/              # Database migrations
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_models.py
│   │   ├── test_services.py
│   │   └── test_utils.py
│   ├── integration/
│   │   ├── test_auth.py
│   │   ├── test_payment.py
│   │   └── test_meal_generation.py
│   └── fixtures/
├── static/                  # Static files
├── templates/               # HTML templates
├── scripts/                 # Utility scripts
├── docs/                    # Documentation
├── .env.example            # Environment example
├── requirements.txt        # Dependencies
├── run.py                  # Application entry point
├── wsgi.py                 # WSGI entry point
└── README.md              # Project documentation
```

## Pasos de Refactorización

### Fase 1: Preparación
1. Crear backup del proyecto actual
2. Crear nueva estructura de directorios
3. Configurar __init__.py files

### Fase 2: Separación de Modelos
1. Dividir models.py en archivos individuales:
   - user.py: User, UserPreferences
   - payment.py: Payment, PricingPlan, SubscriptionTier
   - meal_plan.py: SavedMealPlan, SharedMealPlan, MealPlanShare
   - usage.py: UsageLog, APIKey

### Fase 3: Organización de Rutas
1. Crear blueprints para cada área:
   - auth.py: Login, registro, perfil
   - main.py: Rutas principales, generación de meals
   - admin.py: Panel administrativo
   - payment.py: Procesamiento de pagos
   - share.py: Compartir meal plans

### Fase 4: Servicios y Lógica de Negocio
1. Mover lógica de negocio a servicios:
   - meal_optimizer.py: Generación de meal plans
   - video_generator.py: Creación de videos
   - pdf_generator.py: Generación de PDFs
   - payment_processor.py: Lógica de pagos

### Fase 5: Application Factory Pattern
1. Implementar factory pattern en app/__init__.py
2. Configurar extensiones en extensions.py
3. Centralizar configuración en config/

### Fase 6: Limpieza y Optimización
1. Eliminar archivos duplicados
2. Consolidar utilidades
3. Actualizar imports
4. Revisar y actualizar tests

## Beneficios de la Nueva Estructura

1. **Separación de Responsabilidades**: Cada módulo tiene una responsabilidad clara
2. **Escalabilidad**: Fácil agregar nuevas funcionalidades
3. **Mantenibilidad**: Código más organizado y fácil de mantener
4. **Testabilidad**: Estructura que facilita testing
5. **Reutilización**: Componentes más reutilizables
6. **Mejores Prácticas**: Sigue convenciones de Flask

## Cambios Clave

1. **Application Factory**: Permite múltiples instancias y mejor testing
2. **Blueprints**: Modularización de rutas
3. **Configuración por Entorno**: Separación de configs dev/prod/test
4. **Modelos Separados**: Un archivo por modelo principal
5. **Servicios**: Lógica de negocio separada de rutas
6. **Tests Organizados**: Unit, integration, fixtures separados
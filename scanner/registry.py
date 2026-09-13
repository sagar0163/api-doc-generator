"""Framework registry - metadata, detection and loading for all scanners.

Every scanner module under ``scanner/`` is classified here as either
``supported`` (has a working ``APIScanner`` subclass) or ``placeholder``
(an unimplemented stub).  Only supported scanners participate in
auto-detection; placeholders are listed for transparency and emit a
warning if explicitly requested.
"""

import json
import os
import re


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

# framework id -> metadata.  ``module``/``cls`` are only set for supported
# scanners.  ``detect`` keys into :data:`_DETECTORS`.  ``notes`` reflects
# what the scanner actually does today.
PLACEHOLDER_FRAMEWORKS = {
"apirouter": {
        "name": "FastAPI APIRouter",
        "language": "Python",
        "status": "placeholder",
        "module": None,
        "cls": None,
        "notes": "Stub only - no scanner class; use 'fastapi' (handles @router.*)",
    },
    "axum": {
        "name": "Axum",
        "language": "Rust",
        "status": "placeholder",
        "module": None,
        "cls": None,
        "notes": "Stub only - no scanner class",
    },
    "blueprint": {
        "name": "Flask Blueprint",
        "language": "Python",
        "status": "placeholder",
        "module": None,
        "cls": None,
        "notes": "Stub only - covered by 'flask' (@bp.route)",
    },
    "express_router": {
        "name": "Express Router",
        "language": "JavaScript",
        "status": "placeholder",
        "module": None,
        "cls": None,
        "notes": "Stub only - covered by 'express' (router.*/app.*)",
    },
    "grails": {
        "name": "Grails",
        "language": "Groovy",
        "status": "placeholder",
        "module": None,
        "cls": None,
        "notes": "Stub only - no scanner class",
    },
    "springmvc": {
        "name": "Spring MVC",
        "language": "Java",
        "status": "placeholder",
        "module": None,
        "cls": None,
        "notes": "Stub only - covered by 'spring' (@*Mapping)",
    },
    "vertx": {
        "name": "Vert.x",
        "language": "Java",
        "status": "placeholder",
        "module": None,
        "cls": None,
        "notes": "Stub only - no scanner class",
    },
}

SUPPORTED_FRAMEWORKS = {
    "flask": {
        "name": "Flask",
        "language": "Python",
        "status": "supported",
        "module": "scanner.flask",
        "cls": "FlaskScanner",
        "notes": "@app.route/@bp.route with methods=[]",
    },
    "fastapi": {
        "name": "FastAPI",
        "language": "Python",
        "status": "supported",
        "module": "scanner.fastapi",
        "cls": "FastAPIScanner",
        "notes": "@app/@router.{get,post,...} and @app.route(methods=[])",
    },
    "django": {
        "name": "Django",
        "language": "Python",
        "status": "supported",
        "module": "scanner.django",
        "cls": "DjangoScanner",
        "notes": "urls.py path()/re_path() and @api_view views",
    },
    "drf": {
        "name": "Django REST Framework",
        "language": "Python",
        "status": "supported",
        "module": "scanner.drf",
        "cls": "DRFScanner",
        "notes": "viewsets, APIView classes, @api_view decorators",
    },
    "flask_restful": {
        "name": "Flask-RESTful",
        "language": "Python",
        "status": "supported",
        "module": "scanner.flask_restful",
        "cls": "FlaskRestfulScanner",
        "notes": "Resource subclasses and HTTP verb methods",
    },
    "express": {
        "name": "Express",
        "language": "JavaScript",
        "status": "supported",
        "module": "scanner.express",
        "cls": "ExpressScanner",
        "notes": "app/router.{get,post,...} routes",
    },
    "koa": {
        "name": "Koa",
        "language": "JavaScript",
        "status": "supported",
        "module": "scanner.koa",
        "cls": "KoaScanner",
        "notes": "router.*/app.* routes",
    },
    "hapi": {
        "name": "Hapi",
        "language": "JavaScript",
        "status": "supported",
        "module": "scanner.hapi",
        "cls": "HapiScanner",
        "notes": "server.route({method,path}) + server.{get,post,...}",
    },
    "sails": {
        "name": "Sails.js",
        "language": "JavaScript",
        "status": "supported",
        "module": "scanner.sails",
        "cls": "SailsScanner",
        "notes": "controllers + config/routes.js",
    },
    "adonis": {
        "name": "AdonisJS",
        "language": "JavaScript",
        "status": "supported",
        "module": "scanner.adonis",
        "cls": "AdonisScanner",
        "notes": "start/routes.{ts,js} Route.* decls",
    },
    "nestjs": {
        "name": "NestJS",
        "language": "TypeScript",
        "status": "supported",
        "module": "scanner.nestjs",
        "cls": "NestJSScanner",
        "notes": "@Controller/@Get/@Post decorators",
    },
    "laravel": {
        "name": "Laravel",
        "language": "PHP",
        "status": "supported",
        "module": "scanner.laravel",
        "cls": "LaravelScanner",
        "notes": "routes/{api,web}.php Route::*",
    },
    "symfony": {
        "name": "Symfony",
        "language": "PHP",
        "status": "supported",
        "module": "scanner.symfony",
        "cls": "SymfonyScanner",
        "notes": "#[Route] attrs + config/routes/*.yaml",
    },
    "codeigniter": {
        "name": "CodeIgniter",
        "language": "PHP",
        "status": "supported",
        "module": "scanner.codeigniter",
        "cls": "CodeIgniterScanner",
        "notes": "Controllers method_verb REST style",
    },
    "rails": {
        "name": "Ruby on Rails",
        "language": "Ruby",
        "status": "supported",
        "module": "scanner.rails",
        "cls": "RailsScanner",
        "notes": "config/routes.rb resources + controllers",
    },
    "sinatra": {
        "name": "Sinatra",
        "language": "Ruby",
        "status": "supported",
        "module": "scanner.sinatra",
        "cls": "SinatraScanner",
        "notes": "verb '/path' blocks",
    },
    "phoenix": {
        "name": "Phoenix",
        "language": "Elixir",
        "status": "supported",
        "module": "scanner.phoenix",
        "cls": "PhoenixScanner",
        "notes": "router.ex get/post/resources",
    },
    "play": {
        "name": "Play Framework",
        "language": "Scala",
        "status": "supported",
        "module": "scanner.play",
        "cls": "PlayScanner",
        "notes": "conf/routes + controllers",
    },
    "gin": {
        "name": "Gin",
        "language": "Go",
        "status": "supported",
        "module": "scanner.gin",
        "cls": "GinScanner",
        "notes": "r.{GET,POST,...} + r.Group prefixes",
    },
    "echo": {
        "name": "Echo",
        "language": "Go",
        "status": "supported",
        "module": "scanner.echo",
        "cls": "EchoScanner",
        "notes": "e.{GET,POST,...} + e.Group",
    },
    "fiber": {
        "name": "Fiber",
        "language": "Go",
        "status": "supported",
        "module": "scanner.fiber",
        "cls": "FiberScanner",
        "notes": "app.{Get,Post,...} + app.Group",
    },
    "spring": {
        "name": "Spring Boot",
        "language": "Java",
        "status": "supported",
        "module": "scanner.spring",
        "cls": "SpringBootScanner",
        "notes": "@*Mapping annotations",
    },
    "ktor": {
        "name": "Ktor",
        "language": "Kotlin",
        "status": "supported",
        "module": "scanner.ktor",
        "cls": "KtorScanner",
        "notes": "verb(\"path\") route DSL",
    },
    "aspnet": {
        "name": "ASP.NET Core",
        "language": "C#",
        "status": "supported",
        "module": "scanner.aspnet",
        "cls": "AspNetScanner",
        "notes": "[Http*] + [Route] attributes",
    },
    "actix": {
        "name": "Actix-web",
        "language": "Rust",
        "status": "supported",
        "module": "scanner.actix",
        "cls": "ActixScanner",
        "notes": ".route/.service + #[get] attrs",
    },
    "rocket": {
        "name": "Rocket",
        "language": "Rust",
        "status": "supported",
        "module": "scanner.rocket",
        "cls": "RocketScanner",
        "notes": "#[get(\"path\")] route attrs",
    },
    "vapor": {
        "name": "Vapor",
        "language": "Swift",
        "status": "supported",
        "module": "scanner.vapor",
        "cls": "VaporScanner",
        "notes": "app./router.{get,post,...}",
    },
    "gin_enhanced": {
        "name": "Gin (enhanced)",
        "language": "Go",
        "status": "supported",
        "module": "scanner.gin_enhanced",
        "cls": "GinEnhancedScanner",
        "notes": "Duplicate of 'gin' with middleware detection; kept for compatibility, not auto-detected",
    },
}

FRAMEWORKS = {**SUPPORTED_FRAMEWORKS, **PLACEHOLDER_FRAMEWORKS}

DEFAULT_IGNORE = [".git", "node_modules", "venv", "__pycache__", "dist"]


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def _read(path, max_bytes=1 << 20):
    """Read a file defensively; return '' on any error."""
    try:
        with open(path, "r", errors="ignore") as f:
            return f.read(max_bytes)
    except (OSError, UnicodeDecodeError):
        return ""


def _find_files(project_path, exts):
    """Yield project-relative file paths restricted to dirs we care about."""
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in set(DEFAULT_IGNORE)]
        for file in files:
            if file.endswith(tuple(exts)):
                yield os.path.join(root, file)


def _py_files(project_path):
    return _find_files(project_path, (".py",))


def _package_deps(project_path):
    """Return dependency names from package.json (lowercased)."""
    pkg = os.path.join(project_path, "package.json")
    if not os.path.exists(pkg):
        return set()
    try:
        data = json.loads(_read(pkg))
    except ValueError:
        return set()
    deps = {}
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        deps.update(data.get(section) or {})
    return set(deps.keys())


def _go_mod_has(project_path, needle):
    mod = os.path.join(project_path, "go.mod")
    return needle in _read(mod)


def _has_import(root, exts, module):
    for fp in _find_files(root, exts):
        if re.search(rf"(^|\n)\s*(import|from)\s+{module}", _read(fp)):
            return True
    return False


def _file_has_needle(root, exts, needle):
    for fp in _find_files(root, exts):
        if needle in _read(fp):
            return True
    return False


def _detect_flask(project_path):
    if os.path.exists(os.path.join(project_path, "app.py")):
        if "from flask import" in _read(os.path.join(project_path, "app.py")) \
                or "Flask(" in _read(os.path.join(project_path, "app.py")):
            return True
    return _has_import(project_path, (".py",), "flask")


def _detect_fastapi(project_path):
    if os.path.exists(os.path.join(project_path, "main.py")):
        if "from fastapi import" in _read(os.path.join(project_path, "main.py")) \
                or "FastAPI(" in _read(os.path.join(project_path, "main.py")):
            return True
    return _has_import(project_path, (".py",), "fastapi")


def _detect_django(project_path):
    if os.path.exists(os.path.join(project_path, "manage.py")):
        return True
    if os.path.exists(os.path.join(project_path, "settings.py")):
        return "Django" in _read(os.path.join(project_path, "settings.py"))
    return False


def _detect_drf(project_path):
    return _has_import(project_path, (".py",), "rest_framework")


def _detect_flask_restful(project_path):
    return _has_import(project_path, (".py",), "flask_restful")


def _detect_framework_by_dep(project_path, *needles):
    deps = _package_deps(project_path)
    return any(needle in deps for needle in needles)


_DETECTORS = {
    "flask": _detect_flask,
    "fastapi": _detect_fastapi,
    "django": _detect_django,
    "drf": _detect_drf,
    "flask_restful": _detect_flask_restful,
    "express": lambda p: _detect_framework_by_dep(p, "express"),
    "nestjs": lambda p: _detect_framework_by_dep(p, "@nestjs/core", "@nestjs/common"),
    "koa": lambda p: _detect_framework_by_dep(p, "koa"),
    "hapi": lambda p: _detect_framework_by_dep(p, "@hapi/hapi", "hapi"),
    "adonis": lambda p: _detect_framework_by_dep(p, "@adonisjs/core", "@adonisjs"),
    "sails": lambda p: _detect_framework_by_dep(p, "sails"),
    "gin": lambda p: _go_mod_has(p, "gin-gonic/gin"),
    "echo": lambda p: _go_mod_has(p, "labstack/echo"),
    "fiber": lambda p: _go_mod_has(p, "gofiber/fiber"),
    "actix": lambda p: "actix-web" in _read(os.path.join(p, "Cargo.toml")),
    "rocket": lambda p: "rocket" in _read(os.path.join(p, "Cargo.toml")),
    "aspnet": lambda p: (
        _has_import(p, (".cs",), "Microsoft.AspNetCore")
        or _file_has_needle(p, (".csproj",), "Microsoft.AspNetCore")
    ),
    "spring": lambda p: (
        _has_import(p, (".java",), "org.springframework")
        or "spring-boot" in _read(os.path.join(p, "pom.xml"))
        or "spring-boot" in _read(os.path.join(p, "build.gradle"))
    ),
    "ktor": lambda p: _file_has_needle(
        p,
        (".gradle", ".gradle.kts", ".toml", ".properties", ".xml"),
        "io.ktor",
    ),
    "codeigniter": lambda p: (
        os.path.exists(os.path.join(p, "app", "Controllers"))
        or os.path.exists(os.path.join(p, "application", "controllers"))
    ),
    "laravel": lambda p: (
        os.path.exists(os.path.join(p, "artisan"))
        or os.path.exists(os.path.join(p, "routes", "api.php"))
        or os.path.exists(os.path.join(p, "routes", "web.php"))
    ),
    "symfony": lambda p: (
        os.path.exists(os.path.join(p, "src", "Controller"))
        or "@symfony/framework-bundle" in _read(os.path.join(p, "composer.json"))
    ),
    "phoenix": lambda p: (
        "phoenix" in _read(os.path.join(p, "mix.exs"))
        and any("router.ex" in f for _, _, fs in os.walk(p) for f in fs)
    ),
    "play": lambda p: os.path.exists(os.path.join(p, "conf", "routes")),
    "rails": lambda p: os.path.exists(os.path.join(p, "config", "routes.rb")),
    "sinatra": lambda p: _has_import(p, (".rb",), "sinatra"),
    "vapor": lambda p: "vapor" in _read(os.path.join(p, "Package.swift")),
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def supported_frameworks():
    """Return a dict of framework id -> metadata for working scanners."""
    return dict(SUPPORTED_FRAMEWORKS)


def placeholder_frameworks():
    """Return a dict of framework id -> metadata for stub scanners."""
    return dict(PLACEHOLDER_FRAMEWORKS)


def unique_placeholder_ids(ids):
    """Return placeholder ids, ignoring any ids not known to the registry."""
    return [i for i in ids if i in PLACEHOLDER_FRAMEWORKS]


def detect(project_path):
    """Detect which supported frameworks are present in ``project_path``.

    Returns a list of framework ids (``SUPPORTED_FRAMEWORKS`` only --
    placeholders never participate in auto-detection).  Detection is
    defensive: unrelated/unparseable files never raise.
    """
    detected = []
    for fid in SUPPORTED_FRAMEWORKS:
        detector = _DETECTORS.get(fid)
        if detector is None:
            continue
        try:
            if detector(project_path):
                detected.append(fid)
        except Exception:
            # A broken detector must never break auto-detection.
            continue
    return detected


def get_scanner_class(framework):
    """Return the scanner class for a framework id.

    Raises ``KeyError`` for unknown ids and ``ValueError`` for
    placeholders (which have no implementation).
    """
    if framework not in FRAMEWORKS:
        raise KeyError(f"unknown framework: {framework}")
    meta = FRAMEWORKS[framework]
    if meta["status"] != "supported":
        raise ValueError(
            f"'{framework}' is only a placeholder ({meta['name']}); "
            "no scanner is implemented for it. Run "
            "`apidocgen frameworks --list` to see supported frameworks."
        )
    module = __import__(meta["module"], fromlist=[meta["cls"]])
    return getattr(module, meta["cls"])


def load_scanner(framework, project_path, ignore_dirs=None, include=None):
    """Instantiate the scanner for ``framework`` on ``project_path``."""
    cls = get_scanner_class(framework)
    return cls(
        project_path,
        ignore_dirs=ignore_dirs or DEFAULT_IGNORE,
        include=include,
    )
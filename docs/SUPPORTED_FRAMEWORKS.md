# Supported Frameworks

Only scanners marked **supported** participate in auto-detection.
Scanners marked **placeholder** are stub files with no implementation; they
are excluded from auto-detect (and warned about) so they can never silently
produce garbage. `apidocgen frameworks --list` prints this same split; run
`apidocgen --framework <id>` to force any supported scanner, or
`apidocgen frameworks --list` to see the live registry.

## Supported (functional scanners)

| id             | language      | status      | notes |
|----------------|---------------|-------------|-------|
| flask          | Python        | supported   | `@app.route`/`@bp.route` with `methods=[]` |
| fastapi        | Python        | supported   | `@app`/`@router.{get,post,...}` and `@app.route(methods=[])` |
| django         | Python        | supported   | urls.py `path()`/`re_path()` wired to views; `@api_view` decorated views resolved to their routes |
| drf            | Python        | supported   | viewsets, `APIView` classes, `@api_view` decorators |
| flask_restful  | Python        | supported   | `Resource` subclasses and HTTP verb methods |
| express        | JavaScript    | supported   | `app`/`router.{get,post,...}` routes |
| koa            | JavaScript    | supported   | `router.*`/`app.*` routes |
| hapi           | JavaScript    | supported   | `server.route({method,path})` + `server.{get,post,...}` |
| sails          | JavaScript    | supported   | controllers + `config/routes.js` |
| adonis         | JavaScript    | supported   | `start/routes.{ts,js}` `Route.*` declarations |
| nestjs         | TypeScript    | supported   | `@Controller`/`@Get`/`@Post` decorators |
| laravel        | PHP           | supported   | `routes/{api,web}.php` `Route::*` |
| symfony        | PHP           | supported   | `#[Route]` attributes + `config/routes/*.yaml` |
| codeigniter    | PHP           | supported   | Controllers `method_verb` REST style |
| rails          | Ruby          | supported   | `config/routes.rb` resources + controllers |
| sinatra        | Ruby          | supported   | `verb '/path'` blocks |
| phoenix        | Elixir        | supported   | `router.ex` `get`/`post`/`resources` |
| play           | Scala         | supported   | `conf/routes` + controllers |
| gin            | Go            | supported   | `r.{GET,POST,...}` routes + `r.Group` prefixes |
| echo           | Go            | supported   | `e.{GET,POST,...}` + `e.Group` |
| fiber          | Go            | supported   | `app.{Get,Post,...}` + `app.Group` |
| spring         | Java          | supported   | `@*Mapping` annotations |
| ktor           | Kotlin        | supported   | `verb("path")` route DSL |
| aspnet         | C#            | supported   | `[Http*]` + `[Route]` attributes |
| actix          | Rust          | supported   | `.route`/`.service` + `#[get]` attributes |
| rocket         | Rust          | supported   | `#[get("path")]` route attributes |
| vapor          | Swift         | supported   | `app.`/`router.{get,post,...}` |
| gin_enhanced   | Go            | supported   | duplicate of `gin` with middleware detection; kept for compatibility, **not auto-detected** (a Gin project matches `gin`) |

## Placeholders (stubs - no scanner, excluded from auto-detect)

| id             | language      | status      | notes |
|----------------|---------------|-------------|-------|
| apirouter      | Python        | placeholder | stub only; covered by `fastapi` (`@router.*`) |
| blueprint      | Python        | placeholder | stub only; covered by `flask` (`@bp.route`) |
| express_router | JavaScript    | placeholder | stub only; covered by `express` (`router.*`/`app.*`) |
| grails         | Groovy        | placeholder | stub only |
| springmvc      | Java          | placeholder | stub only; covered by `spring` (`@*Mapping`) |
| vertx          | Java          | placeholder | stub only |
| axum           | Rust          | placeholder | stub only |

## Autodetect notes

- Auto-detection runs every **supported** detector; matching scanners all
  run (e.g. a Django + DRF project runs both `django` and `drf`).
- Unrelated files never cause errors: detection reads marker files
  defensively and scanners are wrapped so a failure degrades gracefully.
- `node_modules`, `venv`, `__pycache__`, `dist`, `.git` and friends are
  skipped by every scanner (configurable via `ignore` in `api-doc.yaml`).
- Placeholders never run and are never detected; a warning explains why.
- If nothing is detected, all supported scanners run as a best effort
  (minus the `gin_enhanced` duplicate).
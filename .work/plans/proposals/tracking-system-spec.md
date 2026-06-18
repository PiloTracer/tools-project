# Especificación: Sistema de Tracking para AI Epic Studio

> **Propósito:** Documentar todos los requisitos de tracking necesarios para incorporar en el sistema de administración de proyectos actual (20% completado).
> **Fuentes:** `.work/plans/strategy_pipeline_tracker.md`, `.work/plans/progress_tracker.md`, `.ai.promote/skills/weekly-review.md`, `.ai.promote/skills/referral-system.md`, `.ai.promote/skills/content-publish.md`

---

## 1. CRM / Pipeline de Ventas (Core)

### 1.1 Entidad: Prospect

| Campo | Tipo | Ejemplo | Reglas |
|-------|------|---------|--------|
| `name` | string | "John Smith" | Required |
| `company` | string | "AcmeCorp" | Required |
| `source` | enum | content / referral / community / inbound / warm_msg / website | Required |
| `stage` | enum (1-9) | 4 | Ver §1.2 |
| `date_first_contact` | date | 2026-06-10 | Required |
| `last_interaction` | date | 2026-06-16 | Auto-set on activity |
| `next_action` | text | "Enviar caso de estudio AIDA" | Required |
| `next_action_date` | date | 2026-06-19 | Optional, para follow-ups |
| `notes` | text | "Le gustó el post de AIDA" | Optional |
| `pipeline_value` | decimal | 35000 | Solo stages 6+ |
| `tags` | string[] | ["fintech", "seed-stage"] | Opcional |
| `created_at` | datetime | — | Auto |
| `updated_at` | datetime | — | Auto |

### 1.2 Etapas del Pipeline (Stage Enum)

| # | Código | Nombre | Descripción | Acción esperada |
|---|--------|--------|-------------|-----------------|
| 1 | `target` | Target | Identificado, no contactado | Espera |
| 2 | `connected` | Connected | Conexión LinkedIn aceptada o email enviado | Enviar Message 2 si no reply en 3d |
| 3 | `engaged` | Engaged | Respondió a DM/email | Nutrir, enviar caso de estudio |
| 4 | `call_scheduled` | Call Scheduled | Reunión en calendario | Preparar discovery call |
| 5 | `call_done` | Call Done | Discovery call completada | Enviar propuesta en 24-48hrs |
| 6 | `proposal_sent` | Proposal Sent | Propuesta enviada | Follow-up en 5d, breakup en 10d |
| 7 | `negotiating` | Negotiating | Discutiendo términos | No descontar, reducir scope |
| 8 | `won` | Won | Contrato firmado + depósito 50% | Ejecutar onboarding |
| 9 | `lost` | Lost | Dijeron no o se silenciaron | Registrar razón |

### 1.3 Reglas de Transición de Etapa

- Stage solo puede avanzar (1→2→3...), excepto lost (puede venir de cualquier stage)
- `won` y `lost` son terminales
- Si un prospecto vuelve después de lost, crear nuevo registro con source = "reactivated"
- Al mover a `won`: trigger checklist de onboarding (§7)

### 1.4 Automatización de Follow-ups (Cadencia)

| Condición | Acción automática |
|-----------|------------------|
| Stage = connected, no actividad en 3d | Flag: "Enviar Message 2 (value-add)" |
| Stage = connected, no actividad en 7d | Flag: "Enviar Message 3 (direct ask)" |
| Stage = connected, no actividad en 14d | Sugerir mover a lost |
| Stage = call_done, no propuesta en 48hrs | Flag: "Enviar propuesta" |
| Stage = proposal_sent, no actividad en 5d | Flag: "Follow-up: checking questions" |
| Stage = proposal_sent, no actividad en 10d | Flag: "Enviar breakup message" |
| Stage = lost | Flag: "Revisitar en 60-90 días" |
| Cualquier stage, no actividad en 30d | Sugerir mover a lost |

---

## 2. Dashboard de Métricas Semanales

### 2.1 Entidad: WeeklyMetrics (una por semana)

| Campo | Tipo | Target |
|-------|------|--------|
| `week_start` | date | — |
| `posts_published` | int | 2 |
| `community_answers` | int | 5+ |
| `warm_messages_sent` | int | 3-5 |
| `profile_views` | int | — |
| `inbound_messages` | int | — |
| `conversations_started` | int | 2+ |
| `calls_scheduled` | int | 1+ |
| `proposals_sent` | int | — |
| `deals_closed` | int | — |
| `pipeline_value` | decimal | — |
| `notes` | text | — |

### 2.2 Pipeline Health Score (cálculo automático)

Usar weekly metrics para calcular 4 scores (1-5):

| Score | Fórmula |
|-------|---------|
| **Awareness** | profile_views >= 50 → 5; >= 20 → 3; <20 → 1 |
| **Interest** | inbound_messages >= 3 → 5; >= 1 → 3; 0 → 1 |
| **Trust** | calls_scheduled >= 1 → 5; conversations >= 1 → 3; 0 → 1 |
| **Decision** | proposals accepted → 5; proposals sent pending → 3; 0 → 1 |

El score más bajo es el **cuello de botella** actual.

### 2.3 Vista Recomendada (Weekly Review)

```
Semana: [date range]
Pipeline Health: Awareness _ / Interest _ / Trust _ / Decision _
Cuello de botella: [lowest score stage]

Métricas:
  Posts: _ / 2
  Inbounds: _ / —
  Warm msgs: _ / 3-5
  Conversaciones: _ / 2+
  Llamadas: _ / 1+
  Propuestas: _ / —
  Cerrados: _ / —

¿Qué funcionó?: [text]
¿Qué no?: [text]
Acción para próxima semana: [text]
```

---

## 3. Tracking de Contenido

### 3.1 Entidad: ContentPost

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | uuid | — |
| `published_at` | datetime | — |
| `platform` | enum | linkedin_feed / linkedin_article / twitter / blog |
| `topic_bucket` | enum | architecture_lesson / ai_in_practice / year_perspective / project_behind_scenes / case_study |
| `hook_style` | enum | question / controversy / result / story |
| `title_or_hook` | text | Primeras líneas |
| `url` | string | Link a la publicación |
| `impressions` | int | — |
| `engagement` | int | Likes + comments + shares |
| `inbounds_generated` | int | Cuántos leads generó |
| `notes` | text | — |

### 3.2 Dashboard de Contenido

Vista agregada:
- Total posts por semana/mes
- Impresiones promedio por topic_bucket
- Engagement rate por hook_style
- Inbounds generados por pieza
- Top 5 posts por engagement

---

## 4. Tracking de Referidos

### 4.1 Entidad: Referral

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | uuid | — |
| `referred_by` | string | Nombre de quien refiere |
| `relationship` | enum | former_boss / former_colleague / vendor / client / friend |
| `contacted_at` | date | Cuando se pidió el referido |
| `prospect_name` | string | Nombre del referido (opcional) |
| `prospect_company` | string | Empresa del referido |
| `status` | enum | promised / intro_made / connected / engaged / converted / declined |
| `result_notes` | text | — |
| `linkedin_rec_requested` | bool | ¿Se pidió recomendación LinkedIn? |
| `linkedin_rec_given` | bool | ¿La dieron? |

### 4.2 Etapas del Referido

| Stage | Descripción |
|-------|-------------|
| `promised` | Dijeron "sí, conozco a alguien" pero no han hecho intro |
| `intro_made` | Te presentaron por email/LinkedIn |
| `connected` | El prospecto aceptó conexión |
| `engaged` | El prospecto respondió |
| `converted` | Se convirtió en cliente |
| `declined` | El referido no era adecuado o no interesó |

---

## 5. Progress Tracker (Plan General)

### 5.1 Entidad: SkillProgress

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `skill_name` | string | Nombre del skill (linkedin-overhaul, case-study-write, etc.) |
| `phase` | int | 1-4 |
| `status` | enum | pending / input_received / in_progress / completed / blocked |
| `inputs_received` | text[] | Lista de insumos |
| `last_updated` | datetime | — |
| `notes` | text | — |
| `next_step` | text | — |

### 5.2 Entidad: InputLog

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `date` | datetime | — |
| `skill` | string | skill_name |
| `input_type` | string | description / document / image / link |
| `description` | text | Qué se recibió |
| `nda_status` | enum | safe / needs_redaction / not_publishable |
| `action_taken` | text | Qué se hizo con el insumo |

---

## 6. Seguimiento NDA

### 6.1 Entidad: NDACheck

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `content_id` | uuid | Referencia al contenido |
| `content_type` | string | case_study / proposal / post / article |
| `check_date` | datetime | — |
| `elements_checked` | json[] | Array de {element: string, publishable: bool, note: string} |
| `verdict` | enum | safe / needs_changes / blocked |
| `approved_by` | string | — |

---

## 7. Onboarding de Cliente (Post-Won)

### 7.1 Checklist (al marcar prospecto como `won`)

| Item | Descripción | Quién |
|------|-------------|-------|
| [ ] Contract signed | Contrato firmado | Tú |
| [ ] 50% deposit received | Depósito recibido | Admin |
| [ ] Kickoff call scheduled | Llamada de inicio | Admin |
| [ ] GitHub repo created | Repositorio creado | Tú |
| [ ] Slack/Discord channel created | Canal de comunicación | Admin |
| [ ] PM tool access granted | Acceso a herramienta de project management | Admin |
| [ ] First milestone defined | Hito 1 con criterios de aceptación | Tú |
| [ ] Weekly check-in scheduled | Reunión semanal recurrente (30 min) | Admin |
| [ ] Invoice reminder set | Recordatorio de facturación por hitos | Admin |
| [ ] Referral asked | "¿A quién más conoces que esté construyendo algo?" | Tú |

---

## 8. Prioridad de Implementación

| Orden | Módulo | Justificación | Esfuerzo estimado |
|-------|--------|---------------|-------------------|
| 1 | CRM Pipeline (Prospect + stages + follow-ups) | Core del negocio, se necesita desde el día 1 | Alto |
| 2 | Weekly Metrics + Health Score | Feedback loop semanal, sin esto no hay mejora | Medio |
| 3 | Content Tracking | Para saber qué contenido funciona | Medio |
| 4 | Referral Tracking | Baja complejidad, útil para medir source de mejores leads | Bajo |
| 5 | Client Onboarding Checklist | Solo necesario después del primer win | Bajo |
| 6 | Progress Tracker (skills) | Útil para AI agent, no crítico para el sistema | Bajo |
| 7 | NDA Audit | Compliance, bajo volumen de datos | Bajo |

---

## 9. Consideraciones Técnicas

- **Base de datos:** PostgreSQL (consistente con el stack del portafolio)
- **Autenticación:** JWT (ya usado en proyectos anteriores)
- **API:** RESTful con FastAPI (mismo stack que AIDA)
- **Frontend:** Dashboard simple con tablas y filtros (Next.js o similar)
- **Mobile:** No necesario en V1
- **Colaboradores:** El admin necesita acceso para actualizar stages, agendar follow-ups, y llevar métricas. Considerar roles: admin (lectura/escritura parcial) vs owner (full access)
- **Notificaciones:** En V1, flags visuales en dashboard. En V2, emails automáticos

### Stack recomendado (consistente con el portafolio):

```
Backend: FastAPI + SQLAlchemy async + PostgreSQL
Frontend: Next.js + Material UI (mismo stack que AIDA)
API: RESTful con BFF pattern (mismo patrón que AIDA)
Auth: JWT
Deploy: Docker
```

# rhdh-plugin-catalog layout

## Files to update

| Location | When to edit |
|----------|----------------|
| `.tekton/oci-plugin-build-pipeline.yaml` | Shared `Pipeline`; most PLRs use `pipelineRef` |
| `.tekton/plugin-catalog-index-*-push.yaml` | Inline `pipelineSpec` (catalog index) |
| `.tekton/plugin-catalog-builder-*-{push,pull}.yaml` | Inline `pipelineSpec` (catalog builder) |
| `.tekton/*-push.yaml` (many components) | Usually `spec.params` only when migration adds pipeline params |
| `.tekton/*-pull.yaml` | Same when present |
| `.tekton/generatePipelineRunsForPlugins.sh` | Heredoc for regenerated PLRs + `*.Containerfile` |
| `.tekton/updateToStableBranch.py` | Version renames only — not Konflux migrations |

Plugin PLRs with `pipelineRef: oci-plugin-build-pipeline` inherit task wiring from the shared pipeline; add PLR `spec.params` when migrations require explicit pipeline parameters.

## Regenerate

```bash
cd .tekton
./generatePipelineRunsForPlugins.sh -v <x.y.z> --nopush
```

## Generator: new pipeline params

Add to the PipelineRun heredoc `spec.params` when `oci-plugin-build-pipeline` gains a param, e.g.:

```yaml
  - name: enable-package-registry-proxy
    value: "true"
```

Do not embed full `pipelineSpec` in the generator.

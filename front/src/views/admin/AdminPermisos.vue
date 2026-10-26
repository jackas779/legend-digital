<script setup>
import { reactive, ref } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import { db } from '../../lib/data'
import { toast } from '../../stores/toast'

const NIVELES = ['—', 'Lectura', 'Lectura/Escritura', 'Administrar']

const matriz = reactive(JSON.parse(JSON.stringify(db.permisos)))
const dirty = ref(false)

function nivelSeleccionado(valor) {
  if (!valor) return '—'
  if (!valor[0]) return '—'
  if (valor[2]) return 'Administrar'
  if (valor[1]) return 'Lectura/Escritura'
  return 'Lectura'
}

function cambiar(rol, modulo, label) {
  matriz[rol][modulo] =
    label === '—'
      ? [false, false, false]
      : label === 'Lectura'
        ? [true, false, false]
        : label === 'Lectura/Escritura'
          ? [true, true, false]
          : [true, true, true]
  dirty.value = true
}

function guardar() {
  for (const rol of db.roles) {
    for (const modulo of db.modulos) {
      db.permisos[rol][modulo.key] = [...matriz[rol][modulo.key]]
    }
  }
  dirty.value = false
  toast('Matriz de permisos actualizada')
}
</script>

<template>
  <div class="card">
    <div class="card-header flex items-center" style="padding-bottom: 18px">
      <div style="flex: 1">
        <div class="card-title"><AppIcon name="key" :size="16" /> Roles × Módulos</div>
        <div class="card-desc">Define qué puede hacer cada rol. Los cambios se aplican al guardar.</div>
      </div>
      <button class="btn" :class="dirty ? 'btn-warning' : 'btn-primary'" @click="guardar">
        <AppIcon name="check" :size="16" /> Guardar cambios
      </button>
    </div>

    <div class="card-body" style="padding: 0 22px 22px">
      <div class="table-wrap">
        <table class="table matriz">
          <thead>
            <tr>
              <th>Rol</th>
              <th v-for="modulo in db.modulos" :key="modulo.key">{{ modulo.label }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rol in db.roles" :key="rol">
              <td><span class="badge badge-secondary">{{ rol }}</span></td>
              <td v-for="modulo in db.modulos" :key="modulo.key">
                <select
                  class="select permiso-select"
                  :value="nivelSeleccionado(matriz[rol][modulo.key])"
                  @change="cambiar(rol, modulo.key, $event.target.value)"
                >
                  <option v-for="nivel in NIVELES" :key="nivel">{{ nivel }}</option>
                </select>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="alert alert-warning" style="margin-top: 16px">
        <span style="flex-shrink: 0; margin-top: 1px"><AppIcon name="alert" :size="17" /></span>
        <div>
          <div class="alert-title">Restricción del sistema</div>
          <div class="alert-body">
            El rol <b>VOTANTE</b> nunca puede obtener permisos de escritura sobre usuarios ni auditoría,
            y el rol <b>AUDITOR</b> es siempre de solo lectura.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.permiso-select {
  width: 118px;
  padding: 5px 26px 5px 8px;
  font-size: 12px;
}
</style>

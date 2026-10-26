<script setup>
import { computed, reactive, ref } from 'vue'
import AppIcon from '../../components/AppIcon.vue'
import AppModal from '../../components/AppModal.vue'
import EstadoBadge from '../../components/EstadoBadge.vue'
import UserAvatar from '../../components/UserAvatar.vue'
import { db } from '../../lib/data'
import { toast } from '../../stores/toast'

const q = ref('')
const estado = ref('TODOS')
const modalAbierto = ref(false)
const editandoId = ref(null)

const form = reactive({
  nombres: '',
  apellidos: '',
  documento: '',
  correo: '',
  rol: 'VOTANTE',
  estado: 'ACTIVO',
  password: '',
})

const usuarios = computed(() => {
  const texto = q.value.toLowerCase().trim()
  return db.usuarios.filter((u) => {
    const coincideEstado = estado.value === 'TODOS' || u.estado === estado.value
    const coincideTexto =
      !texto || `${u.documento} ${u.nombres} ${u.apellidos} ${u.correo}`.toLowerCase().includes(texto)
    return coincideEstado && coincideTexto
  })
})

function abrirNuevo() {
  editandoId.value = null
  Object.assign(form, {
    nombres: '',
    apellidos: '',
    documento: '',
    correo: '',
    rol: 'VOTANTE',
    estado: 'ACTIVO',
    password: '',
  })
  modalAbierto.value = true
}

function abrirEditar(usuario) {
  editandoId.value = usuario.id
  Object.assign(form, {
    nombres: usuario.nombres,
    apellidos: usuario.apellidos,
    documento: usuario.documento,
    correo: usuario.correo,
    rol: usuario.rol,
    estado: usuario.estado,
    password: '',
  })
  modalAbierto.value = true
}

function guardar() {
  if (!form.nombres.trim() || !form.apellidos.trim() || !form.documento.trim() || !form.correo.trim()) {
    toast('Completa los campos obligatorios', 'destructive')
    return
  }

  if (editandoId.value) {
    const usuario = db.usuarios.find((u) => u.id === editandoId.value)
    if (usuario) {
      Object.assign(usuario, {
        nombres: form.nombres.trim(),
        apellidos: form.apellidos.trim(),
        documento: form.documento.trim(),
        correo: form.correo.trim(),
        rol: form.rol,
        estado: form.estado,
      })
    }
    toast('Usuario actualizado correctamente')
  } else {
    if (db.usuarios.some((u) => u.documento === form.documento.trim())) {
      toast('Ya existe un usuario con ese documento', 'destructive')
      return
    }
    db.usuarios.push({
      id: Date.now(),
      nombres: form.nombres.trim(),
      apellidos: form.apellidos.trim(),
      documento: form.documento.trim(),
      correo: form.correo.trim(),
      rol: form.rol,
      estado: form.estado,
      intentos: 0,
    })
    toast('Usuario registrado en el padrón')
  }

  modalAbierto.value = false
}

function alternarSuspension(usuario) {
  const suspender = usuario.estado !== 'SUSPENDIDO'
  const mensaje = suspender
    ? `¿Suspender a ${usuario.nombres}? Perderá el acceso temporalmente.`
    : `¿Reactivar a ${usuario.nombres}?`
  if (!window.confirm(mensaje)) return
  usuario.estado = suspender ? 'SUSPENDIDO' : 'ACTIVO'
  toast(`Usuario ${suspender ? 'suspendido' : 'reactivado'}`)
}

function desactivar(usuario) {
  if (!window.confirm(`¿Desactivar la cuenta de ${usuario.nombres} ${usuario.apellidos}?`)) return
  usuario.estado = 'INACTIVO'
  toast('Cuenta desactivada (borrado lógico)')
}
</script>

<template>
  <div class="card">
    <div class="card-header flex items-center gap-14 toolbar">
      <div style="flex: 1">
        <div class="card-title"><AppIcon name="users" :size="16" /> Cuentas registradas</div>
        <div class="card-desc">CRUD de usuarios del sistema y del padrón electoral</div>
      </div>

      <div class="search-box table-search">
        <AppIcon name="search" :size="15" />
        <input v-model="q" placeholder="Documento, nombre o correo…" />
      </div>

      <select v-model="estado" class="select" style="width: auto">
        <option v-for="opcion in ['TODOS', 'ACTIVO', 'SUSPENDIDO', 'INACTIVO']" :key="opcion">
          {{ opcion }}
        </option>
      </select>

      <button class="btn btn-primary" @click="abrirNuevo">
        <AppIcon name="plus" :size="16" /> Nuevo usuario
      </button>
    </div>

    <div style="padding: 0 22px 22px">
      <div class="table-wrap stack">
        <table class="table">
          <thead>
            <tr>
              <th>Documento</th>
              <th>Usuario</th>
              <th>Rol</th>
              <th>Estado</th>
              <th>Intentos</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr v-for="usuario in usuarios" :key="usuario.id">
              <td data-th="Documento" class="font-mono">{{ usuario.documento }}</td>
              <td data-th="Usuario">
                <div class="flex items-center gap-10">
                  <UserAvatar :nombre="`${usuario.nombres} ${usuario.apellidos}`" :size="32" />
                  <div>
                    <div class="fw-600">{{ usuario.nombres }} {{ usuario.apellidos }}</div>
                    <div class="text-sm text-muted">{{ usuario.correo }}</div>
                  </div>
                </div>
              </td>
              <td data-th="Rol"><span class="badge badge-secondary">{{ usuario.rol }}</span></td>
              <td data-th="Estado"><EstadoBadge :estado="usuario.estado" tipo="usuario" /></td>
              <td data-th="Intentos" class="text-muted">{{ usuario.intentos }}/5</td>
              <td data-th="Acciones">
                <div class="actions">
                  <button class="btn btn-ghost btn-sm btn-icon" title="Editar" @click="abrirEditar(usuario)">
                    <AppIcon name="edit" :size="15" />
                  </button>
                  <button
                    class="btn btn-ghost btn-sm btn-icon"
                    :title="usuario.estado === 'SUSPENDIDO' ? 'Reactivar' : 'Suspender'"
                    @click="alternarSuspension(usuario)"
                  >
                    <AppIcon name="lock" :size="15" />
                  </button>
                  <button
                    class="btn btn-ghost btn-sm btn-icon"
                    style="color: hsl(var(--destructive))"
                    title="Eliminar"
                    @click="desactivar(usuario)"
                  >
                    <AppIcon name="trash" :size="15" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!usuarios.length">
              <td colspan="6" class="text-muted" style="text-align: center; padding: 28px">Sin resultados</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="text-sm text-muted" style="margin-top: 12px">
        {{ usuarios.length }} de {{ db.usuarios.length }} usuarios
      </div>
    </div>
  </div>

  <AppModal
    v-model="modalAbierto"
    :titulo="editandoId ? 'Editar usuario' : 'Registrar usuario'"
    :desc="editandoId ? 'Modifica los datos del usuario. Los cambios quedan en la bitácora.' : 'Crea una cuenta individual en el padrón electoral.'"
    icono="userPlus"
  >
    <div class="field-row">
      <div class="field">
        <label>Nombres</label>
        <input v-model="form.nombres" class="input" placeholder="Ana" />
      </div>
      <div class="field">
        <label>Apellidos</label>
        <input v-model="form.apellidos" class="input" placeholder="Torres" />
      </div>
    </div>

    <div class="field">
      <label>Documento</label>
      <input v-model="form.documento" class="input" placeholder="1015487962" />
    </div>

    <div class="field">
      <label>Correo institucional</label>
      <input v-model="form.correo" class="input" type="email" placeholder="usuario@uni.edu.co" />
    </div>

    <div class="field-row">
      <div class="field">
        <label>Rol</label>
        <select v-model="form.rol" class="select">
          <option v-for="rol in db.roles" :key="rol">{{ rol }}</option>
        </select>
      </div>
      <div class="field">
        <label>Estado</label>
        <select v-model="form.estado" class="select">
          <option v-for="opcion in ['ACTIVO', 'SUSPENDIDO', 'INACTIVO']" :key="opcion">{{ opcion }}</option>
        </select>
      </div>
    </div>

    <div class="field">
      <label>Contraseña <span v-if="!editandoId" class="text-muted">(mín. 8 caracteres)</span></label>
      <input
        v-model="form.password"
        class="input"
        type="password"
        :placeholder="editandoId ? 'Dejar en blanco para no cambiar' : '••••••••'"
      />
    </div>

    <template #footer>
      <button class="btn btn-secondary" @click="modalAbierto = false">Cancelar</button>
      <button class="btn btn-primary" @click="guardar">
        <AppIcon name="check" :size="16" /> Guardar
      </button>
    </template>
  </AppModal>
</template>

<style scoped>
.toolbar {
  padding-bottom: 18px;
  flex-wrap: wrap;
}

.table-search {
  width: 210px;
}

@media (max-width: 1100px) {
  .table-search {
    width: 100%;
  }
}
</style>

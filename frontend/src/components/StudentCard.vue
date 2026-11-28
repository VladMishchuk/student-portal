<script setup>
import { reactive, ref } from 'vue'
import { request } from '../api.js'
import { formatAverage } from '../format.js'

const props = defineProps({
  student: { type: Object, required: true },
  canEdit: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'updated'])

const editing = ref(false)
const saving = ref(false)
const errors = ref({})
const form = reactive({
  last_name: '',
  first_name: '',
})

function startEdit() {
  form.last_name = props.student.last_name
  form.first_name = props.student.first_name
  errors.value = {}
  editing.value = true
}

function cancelEdit() {
  editing.value = false
  errors.value = {}
}

async function saveEdit() {
  saving.value = true
  errors.value = {}
  try {
    const updated = await request(`students/${props.student.id}/`, {
      method: 'PATCH',
      body: {
        last_name: form.last_name,
        first_name: form.first_name,
      },
    })
    editing.value = false
    emit('updated', updated)
  } catch (error) {
    const detail = error.data?.detail ?? error.message
    errors.value = error.status === 400 ? error.data : { detail }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="card">
    <div class="card-header">
      <h2>{{ student.last_name }} {{ student.first_name }}</h2>
      <div class="card-actions">
        <button v-if="canEdit && !editing" type="button" @click="startEdit">
          Редагувати
        </button>
        <button type="button" @click="emit('close')">Закрити</button>
      </div>
    </div>

    <form v-if="editing" class="edit-form" @submit.prevent="saveEdit">
      <label>
        Прізвище
        <input v-model.trim="form.last_name" required maxlength="50" />
      </label>
      <span v-if="errors.last_name" class="error">{{ errors.last_name[0] }}</span>

      <label>
        Ім’я
        <input v-model.trim="form.first_name" required maxlength="50" />
      </label>
      <span v-if="errors.first_name" class="error">{{ errors.first_name[0] }}</span>

      <span v-if="errors.detail" class="error">{{ errors.detail }}</span>
      <div class="edit-actions">
        <button type="submit" :disabled="saving">Зберегти</button>
        <button type="button" @click="cancelEdit">Скасувати</button>
      </div>
    </form>

    <p>Середній бал: {{ formatAverage(student.average) }}</p>

    <table v-if="student.grades?.length">
      <thead>
        <tr>
          <th>Дисципліна</th>
          <th>Бали</th>
          <th>ECTS</th>
          <th>Дата</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="grade in student.grades" :key="grade.id">
          <td>{{ grade.course }}</td>
          <td>{{ grade.score }}</td>
          <td>{{ grade.ects }}</td>
          <td>{{ grade.graded_on }}</td>
        </tr>
      </tbody>
    </table>
    <p v-else>Оцінок ще немає</p>

    <slot />
  </section>
</template>

<style scoped>
.card {
  border: 1px solid #d0d7de;
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.card-actions,
.edit-actions {
  display: flex;
  gap: 0.5rem;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin: 0.75rem 0;
  padding: 0.75rem;
  background-color: #f6f8fa;
  border-radius: 4px;
}

table {
  border-collapse: collapse;
  width: 100%;
  margin: 0.75rem 0;
}

th,
td {
  border: 1px solid #d0d7de;
  padding: 0.4rem 0.6rem;
  text-align: left;
}

.error {
  color: #cf222e;
  font-size: 0.9rem;
}
</style>

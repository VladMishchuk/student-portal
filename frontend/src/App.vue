<script setup>
import { computed, onMounted, ref } from 'vue'
import { request } from './api.js'
import GradeForm from './components/GradeForm.vue'
import StudentCard from './components/StudentCard.vue'
import StudentForm from './components/StudentForm.vue'
import StudentTable from './components/StudentTable.vue'

const me = ref(null)
const students = ref([])
const loading = ref(true)
const error = ref('')
const query = ref('')
const selectedId = ref(null)
const message = ref('')

const found = computed(() => {
  const q = query.value.toLowerCase()
  return students.value.filter((s) =>
    `${s.last_name} ${s.first_name}`.toLowerCase().includes(q),
  )
})

const selected = computed(
  () => students.value.find((s) => s.id === selectedId.value) ?? null,
)

function can(permission) {
  return me.value?.permissions.includes(permission) ?? false
}

async function load() {
  try {
    const [user, page] = await Promise.all([request('me/'), request('students/')])
    me.value = user
    students.value = page.results
  } catch (e) {
    error.value =
      e.status === 403 ? 'Увійдіть на сайт' : 'Не вдалося завантажити список'
  } finally {
    loading.value = false
  }
}

async function gradeCreated(grade) {
  const fresh = await request(`students/${grade.student}/`)
  students.value = students.value.map((s) => (s.id === fresh.id ? fresh : s))
  message.value = `Оцінку ${grade.score} (${grade.ects}) виставлено`
}

function studentCreated(student) {
  students.value.push(student)
  message.value = `Студента ${student.last_name} ${student.first_name} додано`
}

function studentUpdated(updated) {
  students.value = students.value.map((s) => (s.id === updated.id ? updated : s))
  message.value = `Дані студента ${updated.last_name} ${updated.first_name} оновлено`
}

async function remove(student) {
  if (!confirm(`Видалити студента ${student.last_name} ${student.first_name}?`)) {
    return
  }
  try {
    await request(`students/${student.id}/`, { method: 'DELETE' })
    students.value = students.value.filter((s) => s.id !== student.id)
    if (selectedId.value === student.id) {
      selectedId.value = null
    }
    message.value = `Студента ${student.last_name} ${student.first_name} видалено`
  } catch (e) {
    message.value = e.data?.detail ?? e.message
  }
}

onMounted(load)
</script>

<template>
  <p v-if="loading">Завантаження…</p>
  <p v-else-if="error" class="error">
    {{ error }} <a href="/accounts/login/?next=/">Увійти</a>
  </p>
  <template v-else>
    <p>Користувач: {{ me?.username }}</p>
    <p v-if="message" role="status">{{ message }}</p>

    <label class="search">
      Пошук
      <input v-model.trim="query" type="search" @keyup.esc="query = ''" />
    </label>

    <StudentTable
      v-if="found.length"
      :students="found"
      :selected-id="selectedId"
      @select="selectedId = $event.id"
    >
      <template #actions="{ student }">
        <button
          v-if="can('delete_student')"
          type="button"
          @click="remove(student)"
        >
          Видалити
        </button>
      </template>
    </StudentTable>
    <p v-else>Нікого не знайдено</p>

    <Transition name="card">
      <StudentCard
        v-if="selected"
        :key="selected.id"
        :student="selected"
        :can-edit="can('change_student')"
        @close="selectedId = null"
        @updated="studentUpdated"
      >
        <GradeForm
          v-if="can('add_grade')"
          :student-id="selected.id"
          @created="gradeCreated"
        />
      </StudentCard>
    </Transition>

    <StudentForm
      v-if="can('add_student')"
      :group-id="1"
      @created="studentCreated"
    />
  </template>
</template>

<style scoped>
.search {
  display: block;
  margin-bottom: 1rem;
}

.error {
  color: #cf222e;
}

.card-enter-active,
.card-leave-active {
  transition: opacity 0.25s;
}

.card-enter-from,
.card-leave-to {
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .card-enter-active,
  .card-leave-active {
    transition: none;
  }
}
</style>

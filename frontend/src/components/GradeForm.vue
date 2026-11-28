<script setup>
import { reactive, ref } from 'vue'
import { request } from '../api.js'

const props = defineProps({
  studentId: { type: Number, required: true },
})
const emit = defineEmits(['created'])

const today = () => new Date().toISOString().slice(0, 10)
const form = reactive({
  course: '',
  score: null,
  graded_on: today(),
})
const errors = ref({})
const saving = ref(false)

async function submit() {
  saving.value = true
  errors.value = {}
  try {
    const grade = await request('grades/', {
      method: 'POST',
      body: { ...form, student: props.studentId },
    })
    emit('created', grade)
    form.course = ''
    form.score = null
    form.graded_on = today()
  } catch (error) {
    const detail = error.data?.detail ?? error.message
    errors.value = error.status === 400 ? error.data : { detail }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <form class="grade-form" @submit.prevent="submit">
    <h3>Нова оцінка</h3>
    <label>
      Дисципліна
      <input v-model.trim="form.course" required maxlength="100" />
    </label>
    <span v-if="errors.course" class="error">{{ errors.course[0] }}</span>

    <label>
      Бали
      <input v-model.number="form.score" type="number" min="0" max="100" required />
    </label>
    <span v-if="errors.score" class="error">{{ errors.score[0] }}</span>

    <label>
      Дата
      <input v-model="form.graded_on" type="date" required />
    </label>
    <span v-if="errors.graded_on" class="error">{{ errors.graded_on[0] }}</span>

    <span v-if="errors.detail" class="error">{{ errors.detail }}</span>
    <button type="submit" :disabled="saving">Виставити</button>
  </form>
</template>

<style scoped>
.grade-form {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
}

.error {
  color: #cf222e;
  font-size: 0.9rem;
}
</style>

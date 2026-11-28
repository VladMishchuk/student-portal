<script setup>
import { reactive, ref } from 'vue'
import { request } from '../api.js'

const props = defineProps({
  groupId: { type: Number, required: true },
})
const emit = defineEmits(['created'])

const form = reactive({
  first_name: '',
  last_name: '',
})
const errors = ref({})
const saving = ref(false)

async function submit() {
  saving.value = true
  errors.value = {}
  try {
    const student = await request('students/', {
      method: 'POST',
      body: { ...form, group: props.groupId },
    })
    emit('created', student)
    form.first_name = ''
    form.last_name = ''
  } catch (error) {
    const detail = error.data?.detail ?? error.message
    errors.value = error.status === 400 ? error.data : { detail }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <form class="student-form" @submit.prevent="submit">
    <h3>Новий студент</h3>
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
    <button type="submit" :disabled="saving">Додати</button>
  </form>
</template>

<style scoped>
.student-form {
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

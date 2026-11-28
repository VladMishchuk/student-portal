<script setup>
import { formatAverage } from '../format.js'

defineProps({
  students: { type: Array, required: true },
  selectedId: { type: Number, default: null },
})
const emit = defineEmits(['select'])
</script>

<template>
  <table>
    <thead>
      <tr>
        <th>Студент</th>
        <th>Середній бал</th>
        <th>Дії</th>
      </tr>
    </thead>
    <TransitionGroup name="row" tag="tbody">
      <tr
        v-for="student in students"
        :key="student.id"
        :class="{ selected: student.id === selectedId }"
      >
        <td>
          <button type="button" class="link" @click="emit('select', student)">
            {{ student.last_name }} {{ student.first_name }}
          </button>
        </td>
        <td :class="{ empty: student.average === null }">
          {{ formatAverage(student.average) }}
        </td>
        <td><slot name="actions" :student="student" /></td>
      </tr>
    </TransitionGroup>
  </table>
</template>

<style scoped>
table {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 1rem;
}

th,
td {
  border: 1px solid #d0d7de;
  padding: 0.5rem 0.75rem;
  text-align: left;
}

.selected {
  background-color: #eef6ff;
}

.link {
  background: none;
  border: none;
  color: #0969da;
  cursor: pointer;
  font: inherit;
  padding: 0;
  text-decoration: underline;
}

.empty {
  color: #6e7781;
}

.row-enter-active,
.row-leave-active {
  transition: opacity 0.4s;
}

.row-enter-from,
.row-leave-to {
  opacity: 0;
}

.row-move {
  transition: transform 0.4s;
}

@media (prefers-reduced-motion: reduce) {
  .row-enter-active,
  .row-leave-active,
  .row-move {
    transition: none;
  }
}
</style>

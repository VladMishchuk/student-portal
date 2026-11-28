export function formatAverage(average) {
  if (average === null) return '-'
  return average.toLocaleString('uk-UA', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })
}

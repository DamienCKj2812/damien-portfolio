// Native buffers are length-validated on loading. Callers establish each sample
// range from the descriptor or loop bounds before reading. TypeScript cannot
// carry that numeric range proof through indexed typed-array access; keep this
// assertion centralized without adding work to the active animation loops.
export function packedNumber(values: ArrayLike<number>, index: number): number {
  return values[index] as number
}

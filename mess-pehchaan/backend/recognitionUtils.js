/**
 * Calculates the Euclidean distance between two vectors.
 * @param {number[]} vec1 
 * @param {number[]} vec2 
 * @returns {number}
 */
export function calculateEuclideanDistance(vec1, vec2) {
  if (!vec1 || !vec2) {
    throw new Error('Both vectors must be provided');
  }
  if (vec1.length !== vec2.length) {
    throw new Error(`Vectors must have the same length (vec1: ${vec1.length}, vec2: ${vec2.length})`);
  }
  
  let sum = 0;
  for (let i = 0; i < vec1.length; i++) {
    sum += Math.pow(vec1[i] - vec2[i], 2);
  }
  return Math.sqrt(sum);
}

/**
 * Finds the closest matching user for a given captured face embedding.
 * @param {number[]} capturedEmbedding 128-dimensional array
 * @param {Array<{ id: number, name: string, reg_no: string, face_embedding: number[] }>} usersList 
 * @param {number} threshold The distance threshold below which it's a match (default: 0.6)
 * @returns {{ match: boolean, user?: object, distance?: number }}
 */
export function findBestMatch(capturedEmbedding, usersList, threshold = 0.6) {
  if (!capturedEmbedding || !usersList || usersList.length === 0) {
    return { match: false };
  }

  let minDistance = Infinity;
  let bestMatchUser = null;

  for (const user of usersList) {
    try {
      // Postgres double precision[] might come as numbers or string representation depending on parser,
      // but pg driver parses float8[] as JS array of numbers automatically.
      const dist = calculateEuclideanDistance(capturedEmbedding, user.face_embedding);
      if (dist < minDistance) {
        minDistance = dist;
        bestMatchUser = user;
      }
    } catch (err) {
      console.error(`Error comparing with user ${user.reg_no}:`, err.message);
    }
  }

  if (minDistance <= threshold) {
    return {
      match: true,
      user: {
        id: bestMatchUser.id,
        name: bestMatchUser.name,
        reg_no: bestMatchUser.reg_no
      },
      distance: minDistance
    };
  }

  return {
    match: false,
    distance: minDistance === Infinity ? null : minDistance
  };
}

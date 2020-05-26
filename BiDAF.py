#dynamic

from keras.layers import Layer
import tensorflow as tf

class BiAttentionLayer(Layer):

    def __init__(self, **kwargs):
        super(BiAttentionLayer, self).__init__(**kwargs)

    def build(self, input_shape):
        self.shape=input_shape

        self.kernel = self.add_weight(name='kernel',
                                      shape=(3 * input_shape[3],),
                                      initializer='uniform',
                                      trainable=True)
        super(BiAttentionLayer, self).build(input_shape)

    @tf.function
    def build_similarity_matrix(self, context, question):

        similarity_matrix = tf.constant([])
        for i in range(self.shape[2]):
            for j in range(self.shape[2]):
                c = tf.concat([context[i], question[j], tf.multiply(context[i], question[j])], 0)
                alpha = tf.tensordot(self.kernel, c, 1)
                alpha = tf.reshape(alpha, shape=(1,))
                similarity_matrix = tf.concat([similarity_matrix, alpha], 0)

        similarity_matrix = tf.reshape(similarity_matrix, shape=(self.shape[2], self.shape[2]))
        return similarity_matrix

    @tf.function
    def C2Q_Attention(self, question):

        U_A = tf.constant([])

        for j in range(self.shape[2]):
            temp = tf.zeros(shape=(self.shape[3],), dtype=tf.float32)
            for i in range(self.shape[2]):
                c = tf.tensordot(self.attention[j][i], question[i], 0)
                temp += c

            U_A = tf.concat([U_A, temp], 0)

        U_A = tf.reshape(U_A, shape=(self.shape[2], self.shape[3]))

        return U_A

    @tf.function
    def Q2C_Attention(self, context):

        b = tf.reduce_max(self.attention, axis=1, )

        temp = tf.zeros(shape=(self.shape[3],), dtype=tf.float32)

        for i in range(self.shape[2]):
            temp += tf.tensordot(b[i], context[i], 0)

        H_A = tf.constant([])

        for i in range(self.shape[2]):
            H_A = tf.concat([H_A, temp], 0)

        return tf.reshape(H_A, shape=(self.shape[2], self.shape[3]))

    def megamerge(self, context, U_A, H_A):
        G = tf.constant([])
        for t in range(self.shape[2]):
            temp = tf.concat([context[t], U_A[t], tf.multiply(context[t], U_A[t]), tf.multiply(context[t], H_A[t])], 0)
            G = tf.concat([G, temp], 0)
            # G.append(np.concatenate((context[t],U_A[t],np.multiply(context[t],U_A[t]),np.multiply(context[t],H_A[t]))))
        return tf.reshape(G, shape=(self.shape[2], self.shape[3]*4))

    def call(self, x):

        context, question = x[0][0], x[1][0]
        self.similarity_matrix = self.build_similarity_matrix(context, question)
        self.attention = tf.nn.softmax(self.similarity_matrix)
        self.U_A = self.C2Q_Attention(question)
        self.H_A = self.Q2C_Attention(context)
        self.G = self.megamerge(context, self.U_A, self.H_A)

        return self.G

    def compute_output_shape(self, input_shape):
        return (self.shape[2], self.shape[3]*4)

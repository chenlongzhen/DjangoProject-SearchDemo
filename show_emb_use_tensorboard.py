import tensorflow as tf
import numpy as np
import os
from tensorflow.contrib.tensorboard.plugins import projector

##############
# 读取emb数据
##############
emb_path = "./data/basic_emb"
# 文件格式： "word\tv1,v2..."
save_path = "emb_model"
os.makedirs(save_path, exist_ok=True)

emb_vecs = []
words = []
with open(emb_path, "r") as f:
	for line in f:
		segs = line.strip().split("\t")
		word = segs[0]
		vecs = segs[1]

		vec = vecs.split(",")
		emb_vecs.append(vec)
		words.append(word)

embeddings_vectors = np.stack(emb_vecs, axis=0)

print("emb shape is!")
print(embeddings_vectors.shape)


# 将word写入文件
with open(os.path.join(save_path, 'metadata.tsv'), 'w') as f:
	for word in words:
		f.write(word + "\n")

##############
# tensorboard
##############
# Create some variables.
emb = tf.Variable(embeddings_vectors, name='word_embeddings')

# Add an op to initialize the variable.
init_op = tf.global_variables_initializer()

# Add ops to save and restore all the variables.
saver = tf.train.Saver()

# Later, launch the model, initialize the variables and save the
# variables to disk.
with tf.Session() as sess:
	sess.run(init_op)

	# Save the variables to disk.
	save_ckpt_path = saver.save(sess, f"{save_path}/model.ckpt")
	print("Model saved in path: %s" % save_ckpt_path)

	config = projector.ProjectorConfig()
	# One can add multiple embeddings.
	embedding = config.embeddings.add()
	embedding.tensor_name = emb.name
	# Link this tensor to its metadata file (e.g. labels).
	embedding.metadata_path = os.path.join('metadata.tsv')

	# Comment out if you don't want sprites
	#embedding.sprite.image_path = os.path.join(path, 'sprite_4_classes.png')
	#embedding.sprite.single_image_dim.extend([img_data.shape[1], img_data.shape[1]])
	# Saves a config file that TensorBoard will read during startup.
	projector.visualize_embeddings(tf.summary.FileWriter(save_path), config)


# .tsv file written in model_dir/metadata.tsv

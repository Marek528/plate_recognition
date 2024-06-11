import paho.mqtt.client as mqtt

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect("10.42.0.1", 1883, 60)
client.publish("web/change", "car")
async def toggle_smart_device(device_name: str, state: str):
    """Control Home Assistant entity by friendly name or ID"""
    headers = {
        "Authorization": f"Bearer {SMART_HOME_TOKEN}",
        "Content-Type": "application/json",
    }

    # Optional: Map friendly names → entity_id
    name_to_entity = {
        "lights": "light.living_room",
        "lamp": "light.bedroom_lamp",
        "ac": "climate.ac_unit",
        "fan": "fan.desk_fan",
        # Add more as needed
    }

    entity_id = name_to_entity.get(device_name.lower(), device_name)

    service = f"turn_{'on' if state == 'on' else 'off'}"
    url = f"{SMART_HOME_URL}/services/homeassistant/{service}"

    try:
        response = requests.post(
            url,
            headers=headers,
            json={"entity_id": entity_id},
            timeout=10,
        )
        if response.status_code in (200, 201):
            return {"status": "success", "action": service, "entity": entity_id}
        else:
            return {"error": f"HA returned {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}

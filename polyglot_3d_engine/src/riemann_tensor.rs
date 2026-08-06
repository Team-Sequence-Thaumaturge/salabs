use std::mem;

#[no_mangle]
pub extern "C" fn alloc(size: usize) -> *mut f32 {
    let mut buf = Vec::with_capacity(size);
    let ptr = buf.as_mut_ptr();
    mem::forget(buf);
    ptr
}

#[no_mangle]
pub extern "C" fn dealloc(ptr: *mut f32, capacity: usize) {
    unsafe {
        let _buf = Vec::from_raw_parts(ptr, 0, capacity);
    }
}

#[no_mangle]
pub extern "C" fn calculate_riemann_curvature(
    tensor_ptr: *const f32,
    size: usize
) -> f32 {
    let mut total_curvature: f32 = 0.0;

    unsafe {
        let tensor = std::slice::from_raw_parts(tensor_ptr, size);
        for i in 0..size {
            total_curvature += tensor[i] * tensor[i];
        }
    }

    total_curvature.sqrt()
}

#[no_mangle]
pub extern "C" fn calculate_digital_wave_resonance(
    tensor_ptr: *const f32,
    size: usize,
    time: f32
) -> f32 {
    let mut total_resonance: f32 = 0.0;

    unsafe {
        let tensor = std::slice::from_raw_parts(tensor_ptr, size);
        for i in 0..size {
            total_resonance += tensor[i] * (time * tensor[i]).sin();
        }
    }

    total_resonance
}
